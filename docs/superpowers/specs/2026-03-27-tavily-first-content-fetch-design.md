# Tavily-First Content Fetch Design

## Goal

When `TAVILY_API_KEY` is configured, OpenCMO should prefer Tavily for general-purpose URL extraction and web search before falling back to existing crawl-based behavior.

## Scope

- Change monitor URL analysis so initial project context uses Tavily extraction first.
- Change general-purpose content tools to use Tavily extraction first:
  - `crawl_website`
  - `analyze_competitor`
  - blog research article fetch
- Keep Tavily-first search behavior consistent for helper-based search flows.
- Update README to document the new behavior.

## Non-Goals

- Do not replace crawl-based SEO auditing that requires raw HTML structure.
- Do not replace provider-specific GEO/SERP crawls that depend on target result pages.
- Do not change scoring or orchestration logic outside content acquisition.

## Design

Add a shared Tavily extraction helper in `src/opencmo/tools/tavily_helper.py` that:

- checks whether Tavily is available
- extracts page content from a URL
- normalizes returned content into plain text
- returns `None` on failure so callers can fall back cleanly

Callers that currently fetch general page content directly will switch to:

1. Tavily extract if available
2. existing crawl/http fallback if Tavily returns no usable content

Progress messages in monitor initialization should reflect Tavily extraction when used.

## Testing

- Add service tests proving URL analysis uses Tavily extraction before crawl.
- Add service tests proving crawl fallback still works when Tavily extraction is unavailable.
- Add blog writer tests proving article fetch prefers Tavily extract before crawl.

## Docs

Update `README.md` to state that general-purpose URL analysis and web research prefer Tavily when configured, with crawl fallback retained for unsupported or failed cases.
