import asyncio
import json

from agents import function_tool

from opencmo.tools.geo_providers import (
    GEO_PROVIDER_REGISTRY,
    GeoProviderResult,
    compute_share_of_voice,
    get_enabled_providers,
    reset_brand_aliases,
    set_brand_aliases,
)


async def _resolve_brand_context(brand_name: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Look up project-defined aliases and competitors. Empty if no/ambiguous project."""
    try:
        from opencmo import storage
        matches = await storage.find_projects_by_brand(brand_name)
        if len(matches) != 1:
            return [], []
        project = matches[0]
        aliases = list(project.get("aliases") or [])
        competitors_rows = await storage.list_competitors(project["id"])
        competitors = [
            (c["name"], list(c.get("aliases") or []))
            for c in competitors_rows
        ]
        return aliases, competitors
    except Exception:
        return [], []


@function_tool
async def scan_geo_visibility(brand_name: str, category: str) -> str:
    """Scan AI search platforms for brand visibility and compute a GEO score.

    Checks multiple AI platforms (Perplexity, You.com, ChatGPT, Claude, Gemini,
    Kimi, Qwen, DeepSeek, Zhipu GLM, Doubao) for brand mentions, position, and
    sentiment using multiple query templates. Crawl-based providers run by default;
    API-based providers require environment variables to enable.
    Returns a GEO Score (0-100) with breakdown and improvement suggestions.

    Args:
        brand_name: The brand or product name to search for.
        category: The product category (e.g., "web scraping", "project management").
    """
    enabled_providers = get_enabled_providers()
    disabled_providers = [p for p in GEO_PROVIDER_REGISTRY if not p.is_enabled]

    if not enabled_providers:
        return "No GEO providers are enabled. Check your environment configuration."

    aliases, competitors = await _resolve_brand_context(brand_name)
    aliases_token = set_brand_aliases(aliases)
    try:
        return await _run_scan(
            brand_name, category, enabled_providers, disabled_providers,
            brand_aliases=aliases, competitors=competitors,
        )
    finally:
        reset_brand_aliases(aliases_token)


async def _run_scan(
    brand_name: str,
    category: str,
    enabled_providers: list,
    disabled_providers: list,
    *,
    brand_aliases: list[str] | None = None,
    competitors: list[tuple[str, list[str]]] | None = None,
) -> str:
    # Run all enabled providers concurrently. Crawl providers self-serialize
    # via browser_slot; LLM providers each hit a different vendor endpoint.
    # asyncio.create_task() copies the contextvar (alias setup) into each branch.
    async def _check_one(provider):
        try:
            agg = await provider.check_visibility_multi(brand_name, category)
            return provider.name, agg, None
        except Exception as exc:
            return provider.name, None, exc

    raw = await asyncio.gather(*(_check_one(p) for p in enabled_providers))

    aggregated_results = {}
    flat_results: dict[str, GeoProviderResult] = {}
    for name, agg, exc in raw:
        if agg is not None:
            aggregated_results[name] = agg
            flat_results[name] = GeoProviderResult(
                platform=name,
                mentioned=agg.mentioned,
                mention_count=agg.total_mention_count,
                position_pct=agg.best_position_pct,
                content_snippet="",  # snippets are in per_query_results
                error=agg.error,
            )
        else:
            flat_results[name] = GeoProviderResult(
                platform=name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(exc) if exc else "no result",
                source_status="error",
            )

    # Carry source_status from aggregated results onto flat results so the
    # backward-compat scoring path can exclude blocked/empty providers.
    for name, agg in aggregated_results.items():
        flat_results[name].source_status = agg.source_status

    # Compute GEO Score — only count providers that actually observed something.
    usable = [r for r in flat_results.values() if r.source_status == "ok"]
    usable_count = len(usable)
    crawl_success_rate = usable_count / len(enabled_providers) if enabled_providers else 0.0

    # Visibility (0-40): mentioned on how many *usable* platforms.
    platforms_mentioned = sum(1 for r in usable if r.mentioned)
    visibility_score = int(platforms_mentioned / usable_count * 40) if usable_count else 0

    # Position (0-30): earlier mentions = higher score
    position_scores = []
    for r in usable:
        if r.position_pct is not None:
            # 0% position = score 30, 100% = score 0
            position_scores.append(30 * (1 - r.position_pct / 100))
    position_score = (
        int(sum(position_scores) / len(position_scores)) if position_scores else 0
    )

    # Sentiment (0-30): LLM-based analysis of how AI platforms talk about the brand
    sentiment_score: int | None = None
    sentiment_label = "unavailable"
    sentiment_reasoning = "Sentiment analysis unavailable."
    try:
        from opencmo.tools.text_signals import analyze_geo_sentiment

        # Collect snippets from all platforms for sentiment analysis
        sentiment_snippets: dict[str, str] = {}
        for name, agg in aggregated_results.items():
            parts = []
            for qr in agg.per_query_results:
                if qr.content_snippet:
                    parts.append(qr.content_snippet)
            if parts:
                sentiment_snippets[name] = "\n".join(parts)

        if sentiment_snippets:
            signal = await analyze_geo_sentiment(brand_name, sentiment_snippets)
            sentiment_score = signal.score
            sentiment_label = signal.label
            sentiment_reasoning = signal.reasoning
    except Exception as exc:
        sentiment_reasoning = f"Sentiment analysis unavailable: {exc}"

    if crawl_success_rate == 0.0:
        geo_score = None
    else:
        geo_score = visibility_score + position_score + (sentiment_score or 0)

    # Compute share-of-voice across competitors when project context is available.
    sov: dict | None = None
    if competitors:
        sov_snippets: list[str] = []
        for agg in aggregated_results.values():
            for qr in agg.per_query_results:
                if qr.content_snippet and qr.source_status == "ok":
                    sov_snippets.append(qr.content_snippet)
        sov = compute_share_of_voice(sov_snippets, brand_name, brand_aliases, competitors)

    # Persist scan (best-effort, do not block on failure)
    try:
        from opencmo import storage

        platform_results_json = json.dumps(
            {
                name: {
                    "mentioned": r.mentioned,
                    "mention_count": r.mention_count,
                    "position_pct": r.position_pct,
                    "error": r.error,
                    "source_status": r.source_status,
                }
                for name, r in flat_results.items()
            }
        )
        payload = json.loads(platform_results_json)
        payload["_sentiment"] = {
            "score": sentiment_score,
            "label": sentiment_label,
            "reasoning": sentiment_reasoning,
        }
        platform_results_json = json.dumps(payload)
        # save_geo_scan requires a project_id; use project_id=0 as ad-hoc scan
        provider_names = sorted(p.name for p in enabled_providers)
        await storage.save_geo_scan(
            project_id=0,
            geo_score=geo_score,
            visibility_score=visibility_score,
            position_score=position_score,
            sentiment_score=sentiment_score,
            crawl_success_rate=crawl_success_rate,
            platform_results_json=platform_results_json,
            share_of_voice_json=json.dumps(sov) if sov is not None else None,
            params_hash=storage.scan_params_hash(
                "geo", brand_name.lower(), category.lower(), provider_names,
            ),
            window_start=storage.scan_window_start(),
        )
    except Exception:
        pass  # storage persistence is best-effort

    # Build report
    geo_score_display = f"{geo_score}/100" if geo_score is not None else "N/A (Crawl Failed)"
    lines = [
        f"# GEO Visibility Report: {brand_name}",
        f"**Category**: {category}\n",
        f"## GEO Score: {geo_score_display}\n",
        "| Component | Score | Max |",
        "|-----------|-------|-----|",
        f"| Visibility | {visibility_score} | 40 |",
        f"| Position | {position_score} | 30 |",
        f"| Sentiment ({sentiment_label}) | {sentiment_score if sentiment_score is not None else '—'} | 30 |",
        f"| **Total** | **{geo_score_display}** | **100** |",
        "",
        f"**Sentiment Analysis**: {sentiment_reasoning}",
        "",
        f"## Platform Results ({len(enabled_providers)} enabled, {len(disabled_providers)} disabled)\n",
    ]

    if sov is not None:
        share_pct = lambda v: f"{v * 100:.1f}%"  # noqa: E731
        sov_lines = [
            "## Share of Voice",
            "",
            f"Across {sov['total_mentions']} brand-or-competitor mentions in usable AI responses:",
            "",
            "| Brand | Mentions | Share |",
            "|-------|---------:|------:|",
            f"| **{sov['brand']['name']}** | {sov['brand']['mentions']} | {share_pct(sov['brand']['share'])} |",
        ]
        for c in sov["competitors"]:
            sov_lines.append(f"| {c['name']} | {c['mentions']} | {share_pct(c['share'])} |")
        sov_lines.append("")
        # Insert SOV section right before Platform Results for visibility
        platform_idx = next(i for i, line in enumerate(lines) if line.startswith("## Platform Results"))
        lines[platform_idx:platform_idx] = sov_lines

    for name, data in flat_results.items():
        if data.source_status == "error":
            lines.append(f"### {name} [enabled]: ERROR -- {data.error or 'unknown'}\n")
            continue
        if data.source_status == "blocked":
            lines.append(
                f"### {name} [enabled]: BLOCKED — provider returned a captcha/anti-bot page; not counted in scoring\n"
            )
            continue
        if data.source_status == "empty":
            lines.append(
                f"### {name} [enabled]: EMPTY — provider returned no usable content (likely JS-rendered SPA); not counted in scoring\n"
            )
            continue
        status = "FOUND" if data.mentioned else "NOT FOUND"
        lines.append(f"### {name} [enabled]: {status}")
        if data.mentioned:
            lines.append(f"- Total mentions: {data.mention_count}")
            if data.position_pct is not None:
                lines.append(
                    f"- Best mention position: {data.position_pct}% through response"
                )

        # Show per-query breakdown if available
        agg = aggregated_results.get(name)
        if agg and len(agg.per_query_results) > 1:
            lines.append(f"- Queries checked: {len(agg.per_query_results)}")
            for qr in agg.per_query_results:
                q_status = "✅" if qr.mentioned else "❌"
                q_mentions = f" ({qr.mention_count} mentions)" if qr.mentioned else ""
                lines.append(f"  - {q_status} `{qr.query}`{q_mentions}")
        lines.append("")

    if disabled_providers:
        lines.append("## Disabled Platforms\n")
        for p in disabled_providers:
            env_hint = ", ".join(p.auth_env_vars) if p.auth_env_vars else "N/A"
            extra = ""
            if p.name == "ChatGPT":
                extra = " (also requires OPENCMO_GEO_CHATGPT=1)"
            elif p.name == "Claude":
                extra = " (also requires `anthropic` package)"
            elif p.name == "Gemini":
                extra = " (also requires `google-generativeai` package)"
            lines.append(f"- **{p.name}**: set {env_hint}{extra} to enable")
        lines.append("")

    lines.extend(
        [
            "## Raw Context (for agent analysis)\n",
            "Below are content snippets from each platform for the agent to analyze sentiment and context:\n",
        ]
    )
    for name in aggregated_results:
        agg = aggregated_results[name]
        for qr in agg.per_query_results:
            snippet = qr.content_snippet
            if snippet:
                lines.append(f"### {name} — `{qr.query}`\n{snippet[:3000]}\n")

    return "\n".join(lines)
