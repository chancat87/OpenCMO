from agents import function_tool
from crawl4ai import AsyncWebCrawler


def _extract_markdown(result) -> str:
    """Safely extract markdown string from CrawlResult.

    result.markdown may be str, None, or MarkdownGenerationResult.
    """
    md = result.markdown
    if md is None:
        return ""
    if isinstance(md, str):
        return md
    # MarkdownGenerationResult — prefer .raw_markdown, fallback to str()
    if hasattr(md, "raw_markdown"):
        return md.raw_markdown or ""
    return str(md)


async def fetch_url_content(
    url: str,
    *,
    max_chars: int | None = None,
    tavily_extract_depth: str = "advanced",
) -> tuple[str, str]:
    """Fetch page content with Tavily-first fallback to crawl4ai."""
    from opencmo.tools.tavily_helper import tavily_extract

    content = await tavily_extract(
        url,
        extract_depth=tavily_extract_depth,
        format="markdown",
    )
    source = "tavily"

    if not content:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
        content = _extract_markdown(result)
        source = "crawl4ai"

    if max_chars is not None and len(content) > max_chars:
        content = content[:max_chars]

    return content, source


@function_tool
async def crawl_website(url: str) -> str:
    """Crawl a website and return its content as markdown.

    Args:
        url: The URL of the website to crawl.
    """
    try:
        content, _source = await fetch_url_content(url)
        if len(content) > 10000:
            content = content[:10000] + "\n\n... [content truncated at 10000 characters]"
        return content
    except Exception as e:
        return f"Failed to crawl {url}: {e}"
