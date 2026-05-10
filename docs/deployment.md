# Deployment Checklist

This checklist is for publishing OpenCMO to GitHub and deploying it on a public server. Do not commit real secrets.

## Recommended Path

Use Docker Compose for the first production deployment. It keeps the frontend build, Python runtime, persistent data volume, and restart policy in one repeatable unit. Use a plain virtualenv only when the server cannot run Docker.

## Required Inputs

- GitHub repository: `https://github.com/study8677/OpenCMO.git`
- Server SSH host, user, and key path
- Public domain name and DNS A/AAAA records pointing to the server
- Production environment file stored on the server, not in Git
- `OPENCMO_WEB_TOKEN` with a strong random value
- `OPENAI_API_KEY` or compatible provider keys
- Optional provider keys: Tavily, PageSpeed, DataForSEO, Anthropic, Google AI, SMTP
- Persistent data path for the SQLite database and generated artifacts

## Docker Compose Deployment

1. Build and test locally:

   ```bash
   pytest tests/test_web.py
   cd frontend && npm run build
   ```

2. Push a reviewed branch or merge commit to GitHub.

3. On the server, clone or pull the repository:

   ```bash
   git clone https://github.com/study8677/OpenCMO.git
   cd OpenCMO
   ```

4. Create `.env` on the server with production values:

   ```bash
   OPENCMO_WEB_TOKEN=<strong-random-token>
   OPENCMO_WEB_HOST=0.0.0.0
   OPENCMO_DB_PATH=/data/data.db
   OPENAI_API_KEY=<provider-key>
   ```

5. Start the app:

   ```bash
   docker compose up -d --build
   docker compose logs -f opencmo
   ```

6. Put Nginx or Caddy in front of port `8080` for TLS and the public domain. Keep port `8080` firewalled from the open internet if the reverse proxy is on the same host.

## Virtualenv Alternative

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -e ".[all]"
cd frontend && npm ci && npm run build && cd ..
OPENCMO_WEB_HOST=0.0.0.0 OPENCMO_WEB_TOKEN=<strong-random-token> opencmo-web
```

For a long-running virtualenv deployment, create a `systemd` service with `WorkingDirectory` set to the repo, `EnvironmentFile` pointing to the server-only `.env`, and `ExecStart` pointing to `.venv/bin/opencmo-web`.

## Reverse Proxy

Terminate TLS at the reverse proxy and pass traffic to `127.0.0.1:8080`.

Example Nginx location:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## Backup and Rollback

- Back up the Docker volume or the path containing `OPENCMO_DB_PATH` before each deploy.
- Keep the previous Git commit SHA and image build available.
- Roll back with `git checkout <previous-sha> && docker compose up -d --build`.
- Verify `/api/v1/health` after every deploy.

## Security Notes

- Never commit `.env`, API keys, SMTP passwords, or `OPENCMO_WEB_TOKEN`.
- Set `OPENCMO_WEB_TOKEN` before exposing workspace routes on a public server.
- Public endpoints intentionally remain available for the marketing site: health, waitlist, GitHub stats, site stats, and login.
