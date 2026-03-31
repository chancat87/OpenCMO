# Repository Guidelines

## Project Structure & Module Organization
`src/opencmo/` contains the Python application: `agents/` for specialist agent definitions, `tools/` for crawl/search/SEO/GEO utilities, `web/` for the FastAPI dashboard and legacy templates, and `storage.py`/`service.py` for persistence and orchestration. `tests/` holds the pytest suite. `frontend/src/` contains the React SPA, split into `pages/`, `components/`, `hooks/`, `api/`, and `i18n/`. Static images and screenshots live in `assets/`, and longer design notes live in `docs/`.

## Build, Test, and Development Commands
Set up the backend with `pip install -e ".[all]"` and initialize crawling support with `crawl4ai-setup`. Copy `.env.example` to `.env` before running anything that needs API keys.

- `opencmo`: start the CLI workflow.
- `opencmo-web`: run the FastAPI dashboard on `http://127.0.0.1:8080`.
- `cd frontend && npm install && npm run dev`: run the Vite SPA on `http://127.0.0.1:5173/app/` with API proxying.
- `cd frontend && npm run build`: produce the SPA bundle that `/app` serves from `frontend/dist`.
- `pytest`: run the full Python test suite.
- `pytest tests/test_web.py`: run the web/API regression tests only.

## Coding Style & Naming Conventions
Use 4-space indentation in Python and keep modules/functions in `snake_case`. React components and page files use `PascalCase`; hooks use `useX`; shared API helpers stay in `frontend/src/api/`. Follow the existing style in the repo: type annotations in Python where useful, strict TypeScript, double quotes and semicolons in frontend files, and small focused modules instead of large mixed-responsibility files.

## Testing Guidelines
This repo uses `pytest`, including async tests with `@pytest.mark.asyncio`. Add or update tests in `tests/test_<area>.py` alongside every backend change, especially for storage, web routes, and provider integrations. There is no dedicated frontend test runner yet, so at minimum verify `npm run build` after SPA changes and add backend route tests when UI work depends on new API behavior.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit prefixes such as `feat:`, `docs:`, and `style:`. Keep commit subjects short and imperative, for example `feat: add GEO provider fallback`. PRs should explain user-visible impact, list verification steps, link related issues, and include screenshots for dashboard or graph changes.

## Configuration & Security Tips
Keep secrets in `.env` or the settings UI, never in tracked files. Use `OPENCMO_WEB_TOKEN` when exposing the dashboard beyond localhost, and avoid committing populated database or generated frontend build artifacts unless the change explicitly requires them.

## Production Deployment (BWG Server)

| Item | Value |
|------|-------|
| Host | `bwg` (SSH alias) |
| IP | `97.64.16.217` |
| Project path | `/opt/OpenCMO` |
| Python env | `/opt/OpenCMO/.venv` (venv) |
| Entry point | `/opt/OpenCMO/.venv/bin/opencmo-web` |
| Service port | `8080` |

### Deploy procedure

```bash
# 1. Pull latest code
ssh bwg "cd /opt/OpenCMO && git pull origin main"

# 2. Reinstall Python package (in venv)
ssh bwg "cd /opt/OpenCMO && source .venv/bin/activate && pip install -e ."

# 3. Build frontend LOCALLY (server has insufficient memory for vite build)
cd frontend && npm run build

# 4. Upload dist to server
scp -r frontend/dist/ bwg:/opt/OpenCMO/frontend/dist/

# 5. Restart service
ssh bwg "pkill -f opencmo-web; sleep 1; cd /opt/OpenCMO && source .venv/bin/activate && nohup opencmo-web > /tmp/opencmo.log 2>&1 &"

# 6. Verify
ssh bwg "curl -s http://127.0.0.1:8080/api/v1/health"
```

### Important notes
- Server memory is limited — **frontend must be built locally** and uploaded via `scp`.
- The Python package uses a **venv** at `.venv`, not the system Python. Always `source .venv/bin/activate` before pip install or running commands.
- Use `pip install -e .` (without `[all]`) — some optional deps (`browser-use`) don't have wheels for the server's platform.
- Logs are written to `/tmp/opencmo.log`.
