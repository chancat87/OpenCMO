# Tavily-First Content Fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make general-purpose content fetching Tavily-first across monitor URL analysis and shared content tools, with existing crawl fallbacks preserved.

**Architecture:** Add a shared Tavily extraction helper and route general-purpose fetch callers through it before their existing crawl-based logic. Keep HTML-dependent and provider-specific crawls untouched.

**Tech Stack:** Python, pytest, Tavily SDK, crawl4ai

---

### Task 1: Shared Tavily extraction helper

**Files:**
- Modify: `src/opencmo/tools/tavily_helper.py`
- Test: `tests/test_service.py`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_analyze_url_prefers_tavily_extract():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_service.py::test_analyze_url_prefers_tavily_extract -v`
Expected: FAIL because URL analysis still calls crawl4ai first.

- [ ] **Step 3: Write minimal implementation**

```python
async def tavily_extract(url: str, *, include_images: bool = False) -> str | None:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_service.py::test_analyze_url_prefers_tavily_extract -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_service.py src/opencmo/tools/tavily_helper.py
git commit -m "feat: prefer tavily extraction for url analysis"
```

### Task 2: General-purpose callers

**Files:**
- Modify: `src/opencmo/service.py`
- Modify: `src/opencmo/tools/crawl.py`
- Modify: `src/opencmo/tools/competitor.py`
- Modify: `src/opencmo/tools/blog_writer.py`
- Test: `tests/test_service.py`
- Test: `tests/test_blog_writer.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_crawl_fallback_used_when_tavily_extract_unavailable():
    ...
```

```python
@pytest.mark.asyncio
async def test_research_topic_prefers_tavily_extract():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_service.py tests/test_blog_writer.py -v`
Expected: FAIL on new Tavily-first expectations.

- [ ] **Step 3: Write minimal implementation**

```python
content = await tavily_extract(url)
if not content:
    content = await existing_crawl_logic(url)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_service.py tests/test_blog_writer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_service.py tests/test_blog_writer.py src/opencmo/service.py src/opencmo/tools/crawl.py src/opencmo/tools/competitor.py src/opencmo/tools/blog_writer.py
git commit -m "feat: use tavily-first content fetching"
```

### Task 3: Documentation and verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

```md
OpenCMO now prefers Tavily for general-purpose URL analysis and web research when `TAVILY_API_KEY` is configured, and falls back to crawl-based fetching when Tavily is unavailable or returns no usable content.
```

- [ ] **Step 2: Run verification**

Run: `pytest tests/test_service.py tests/test_blog_writer.py -v`
Expected: PASS

Run: `python -m compileall src`
Expected: exit 0

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document tavily-first fetch behavior"
```
