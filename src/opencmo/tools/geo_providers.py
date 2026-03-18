"""GEO provider architecture for multi-platform AI visibility scanning."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown

# ---------------------------------------------------------------------------
# Conditional imports for API-based providers
# ---------------------------------------------------------------------------

try:
    import anthropic

    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai

    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class GeoProviderResult:
    platform: str
    mentioned: bool
    mention_count: int
    position_pct: float | None  # first mention position %, None if not mentioned
    content_snippet: str  # <=2000 chars
    error: str | None


# ---------------------------------------------------------------------------
# Shared text analysis helper
# ---------------------------------------------------------------------------


def _analyze_text(content: str, brand_name: str) -> tuple[bool, int, float | None]:
    """Analyze text for brand mentions.

    Returns:
        (mentioned, mention_count, position_pct) where position_pct is the
        percentage through the text where the first mention appears, or None.
    """
    content_lower = content.lower()
    brand_lower = brand_name.lower()

    mentioned = brand_lower in content_lower
    mention_count = content_lower.count(brand_lower)

    position_pct: float | None = None
    if mentioned and content_lower:
        first_idx = content_lower.index(brand_lower)
        position_pct = round(first_idx / len(content_lower) * 100, 1)

    return mentioned, mention_count, position_pct


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class GeoProvider(ABC):
    name: str
    status: str  # "enabled" | "disabled"
    requires_auth: bool
    auth_env_vars: list[str]

    @property
    def is_enabled(self) -> bool:
        if self.status == "disabled":
            return False
        if self.requires_auth:
            return all(os.environ.get(v) for v in self.auth_env_vars)
        return True

    @abstractmethod
    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult: ...


# ---------------------------------------------------------------------------
# Crawl-based providers
# ---------------------------------------------------------------------------


class PerplexityProvider(GeoProvider):
    name = "Perplexity"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        url = f"https://www.perplexity.ai/search?q=best+{category.replace(' ', '+')}+tools"
        try:
            async with AsyncWebCrawler() as crawler:
                crawl_result = await crawler.arun(url=url)
                content = _extract_markdown(crawl_result)
                mentioned, mention_count, position_pct = _analyze_text(
                    content, brand_name
                )
                return GeoProviderResult(
                    platform=self.name,
                    mentioned=mentioned,
                    mention_count=mention_count,
                    position_pct=position_pct,
                    content_snippet=content[:2000],
                    error=None,
                )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
            )


class YouDotComProvider(GeoProvider):
    name = "You.com"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        url = f"https://you.com/search?q=best+{category.replace(' ', '+')}+tools"
        try:
            async with AsyncWebCrawler() as crawler:
                crawl_result = await crawler.arun(url=url)
                content = _extract_markdown(crawl_result)
                mentioned, mention_count, position_pct = _analyze_text(
                    content, brand_name
                )
                return GeoProviderResult(
                    platform=self.name,
                    mentioned=mentioned,
                    mention_count=mention_count,
                    position_pct=position_pct,
                    content_snippet=content[:2000],
                    error=None,
                )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
            )


# ---------------------------------------------------------------------------
# API-based providers
# ---------------------------------------------------------------------------

_API_QUERY_TEMPLATE = (
    "What are the best {category} tools? List the top options with brief descriptions."
)


class ChatGPTProvider(GeoProvider):
    name = "ChatGPT"
    status = "disabled"
    requires_auth = True
    auth_env_vars = ["OPENAI_API_KEY"]

    @property
    def is_enabled(self) -> bool:
        return (
            os.environ.get("OPENCMO_GEO_CHATGPT") == "1"
            and bool(os.environ.get("OPENAI_API_KEY"))
        )

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": _API_QUERY_TEMPLATE.format(category=category),
                    }
                ],
                max_tokens=1024,
            )
            content = response.choices[0].message.content or ""
            mentioned, mention_count, position_pct = _analyze_text(
                content, brand_name
            )
            return GeoProviderResult(
                platform=self.name,
                mentioned=mentioned,
                mention_count=mention_count,
                position_pct=position_pct,
                content_snippet=content[:2000],
                error=None,
            )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
            )


class ClaudeProvider(GeoProvider):
    name = "Claude"
    status = "disabled"
    requires_auth = True
    auth_env_vars = ["ANTHROPIC_API_KEY"]

    @property
    def is_enabled(self) -> bool:
        if not _HAS_ANTHROPIC:
            return False
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        try:
            client = anthropic.AsyncAnthropic()
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": _API_QUERY_TEMPLATE.format(category=category),
                    }
                ],
            )
            content = response.content[0].text if response.content else ""
            mentioned, mention_count, position_pct = _analyze_text(
                content, brand_name
            )
            return GeoProviderResult(
                platform=self.name,
                mentioned=mentioned,
                mention_count=mention_count,
                position_pct=position_pct,
                content_snippet=content[:2000],
                error=None,
            )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
            )


class GeminiProvider(GeoProvider):
    name = "Gemini"
    status = "disabled"
    requires_auth = True
    auth_env_vars = ["GOOGLE_AI_API_KEY"]

    @property
    def is_enabled(self) -> bool:
        if not _HAS_GENAI:
            return False
        return bool(os.environ.get("GOOGLE_AI_API_KEY"))

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        try:
            genai.configure(api_key=os.environ["GOOGLE_AI_API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async(
                _API_QUERY_TEMPLATE.format(category=category)
            )
            content = response.text or ""
            mentioned, mention_count, position_pct = _analyze_text(
                content, brand_name
            )
            return GeoProviderResult(
                platform=self.name,
                mentioned=mentioned,
                mention_count=mention_count,
                position_pct=position_pct,
                content_snippet=content[:2000],
                error=None,
            )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
            )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GEO_PROVIDER_REGISTRY: list[GeoProvider] = [
    PerplexityProvider(),
    YouDotComProvider(),
    ChatGPTProvider(),
    ClaudeProvider(),
    GeminiProvider(),
]
