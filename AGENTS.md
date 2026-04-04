# AGENTS.md

## Architecture at a Glance

```
Frontend (React 19 + Vite)  ←→  FastAPI /api/v1/  ←→  SQLite (WAL)
                                      ↓
                              Background Worker
                                      ↓
                    ┌─────── 6-Stage Monitoring Pipeline ───────┐
                    │ 1. Context Build (crawl + 3-role AI debate)│
                    │ 2. Signal Collect (SEO/GEO/Community/SERP) │
                    │ 3. Signal Normalize                        │
                    │ 4. Domain Review (4 AI analysts)           │
                    │ 5. Strategy Synthesis                      │
                    │ 6. Persist & Publish                       │
                    └────────────────────────────────────────────┘
```

## Key Directories

| Path | Role |
|------|------|
| `src/opencmo/agents/` | 25+ specialist agents (CMO orchestrator + platform experts). Names must be ASCII — no Chinese. |
| `src/opencmo/tools/` | Crawl, search, SEO audit, GEO detection, community providers, SERP tracking |
| `src/opencmo/services/` | Domain services: intelligence (AI debate), approval, monitoring |
| `src/opencmo/background/` | Worker + executor registry (scan, report, graph expansion) |
| `src/opencmo/storage/` | Async SQLite, 30+ tables, no ORM |
| `src/opencmo/web/` | FastAPI app, routers, SSE chat, BYOK middleware |
| `src/opencmo/llm.py` | Centralized LLM client: ContextVar isolation, retry + backoff, model resolution |
| `frontend/src/` | React SPA: pages/, components/, hooks/ (TanStack Query), api/, i18n/ (EN/ZH/JA/KO/ES) |

## Critical Patterns

- **LLM calls**: Always use `llm.chat_completion_messages()` for retry. Never call `client.chat.completions.create()` directly.
- **Agent names**: ASCII only (`Zhihu Expert`, not `知乎专家`). openai-agents generates `transfer_to_{name}` tool names.
- **Timestamps**: SQLite stores UTC. Frontend must use `utcDate()` from `utils/time.ts` to parse.
- **Community search**: Tavily → crawl4ai Google scrape fallback. Skip category queries when category is placeholder `"auto"`.
- **BYOK**: Per-request API keys via `X-User-Keys` header → ContextVar. Background tasks capture and restore keys.
- **SPA routing**: No `AnimatePresence key={pathname}` in AppShell — causes full remount and breaks query cache.

## Commands

```bash
# Backend
pip install -e ".[all]"        # Install
opencmo-web                    # Run (port 8080)
pytest tests/                  # Test
ruff check src/ tests/         # Lint

# Frontend
cd frontend && npm install
npm run dev                    # Dev (port 5173, proxies /api → 8080)
npm run build                  # Prod build

# Deploy to BWG (97.64.16.217, SSH port 2222)
cd frontend && npm run build   # Build locally (server OOMs)
rsync -avz --delete frontend/dist/ root@97.64.16.217:/opt/OpenCMO/frontend/dist/ -e "ssh -p 2222"
ssh -p 2222 root@97.64.16.217 "cd /opt/OpenCMO && git pull && source .venv/bin/activate && pip install -e . -q && pkill -f opencmo-web; sleep 1; nohup opencmo-web > /tmp/opencmo.log 2>&1 &"
```

## Coding Conventions

- **Python**: snake_case, 4-space indent, type hints where useful, line length 120 (ruff)
- **TypeScript**: strict mode, PascalCase components, useX hooks, double quotes
- **Commits**: `feat:` / `fix:` / `docs:` prefix, short imperative subject
- **i18n**: All user-facing strings via translation keys (EN/ZH/JA/KO/ES). Never hardcode.
- **Secrets**: `.env` or settings UI only. Never commit API keys or `.db` files.
