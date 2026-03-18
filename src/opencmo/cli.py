import asyncio
import shlex

from dotenv import load_dotenv
from agents import Runner

from opencmo.agents.cmo import cmo_agent


async def _handle_monitor(args: list[str]) -> str:
    """Handle /monitor subcommands."""
    from opencmo import storage

    if not args:
        return "Usage: /monitor add|list|remove|run|history ..."

    sub = args[0]

    if sub == "add":
        # /monitor add <brand> <url> <category> [--type full] [--cron "0 9 * * *"]
        if len(args) < 4:
            return "Usage: /monitor add <brand_name> <url> <category> [--type full|seo|geo|community] [--cron '0 9 * * *']"
        brand, url, category = args[1], args[2], args[3]
        job_type = "full"
        cron_expr = "0 9 * * *"
        i = 4
        while i < len(args):
            if args[i] == "--type" and i + 1 < len(args):
                job_type = args[i + 1]
                i += 2
            elif args[i] == "--cron" and i + 1 < len(args):
                cron_expr = args[i + 1]
                i += 2
            else:
                i += 1

        project_id = await storage.ensure_project(brand, url, category)
        job_id = await storage.add_scheduled_job(project_id, job_type, cron_expr)
        return f"Monitor #{job_id} created: {brand} ({url}) — {job_type} scan, cron: {cron_expr}"

    elif sub == "list":
        jobs = await storage.list_scheduled_jobs()
        if not jobs:
            return "No monitors configured. Use /monitor add to create one."
        lines = ["| ID | Brand | URL | Type | Cron | Enabled | Last Run |",
                 "|----|-------|-----|------|------|---------|----------|"]
        for j in jobs:
            lines.append(
                f"| {j['id']} | {j['brand_name']} | {j['url'][:30]} | {j['job_type']} "
                f"| {j['cron_expr']} | {'Yes' if j['enabled'] else 'No'} | {j['last_run_at'] or 'never'} |"
            )
        return "\n".join(lines)

    elif sub == "remove":
        if len(args) < 2:
            return "Usage: /monitor remove <id>"
        job_id = int(args[1])
        ok = await storage.remove_scheduled_job(job_id)
        return f"Monitor #{job_id} removed." if ok else f"Monitor #{job_id} not found."

    elif sub == "run":
        if len(args) < 2:
            return "Usage: /monitor run <id>"
        job_id = int(args[1])
        jobs = await storage.list_scheduled_jobs()
        job = next((j for j in jobs if j["id"] == job_id), None)
        if not job:
            return f"Monitor #{job_id} not found."

        from opencmo.scheduler import run_scheduled_scan
        print(f"Running {job['job_type']} scan for {job['brand_name']}...")
        await run_scheduled_scan(job["project_id"], job["job_type"], job_id)
        return f"Scan complete for monitor #{job_id}."

    elif sub == "history":
        job_id = int(args[1]) if len(args) > 1 else None
        if job_id:
            jobs = await storage.list_scheduled_jobs()
            job = next((j for j in jobs if j["id"] == job_id), None)
            if not job:
                return f"Monitor #{job_id} not found."
            latest = await storage.get_latest_scans(job["project_id"])
            lines = [f"Latest scans for {job['brand_name']}:"]
            for scan_type, data in latest.items():
                if data:
                    lines.append(f"  {scan_type}: {data}")
                else:
                    lines.append(f"  {scan_type}: no data")
            return "\n".join(lines)
        else:
            return "Usage: /monitor history <id>"

    return f"Unknown subcommand: {sub}"


async def _handle_status() -> str:
    """Handle /status command."""
    from opencmo import storage

    projects = await storage.list_projects()
    if not projects:
        return "No projects tracked yet. Use /monitor add to start."

    lines = ["# Project Status\n"]
    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        lines.append(f"## {p['brand_name']} ({p['url']})")
        seo = latest.get("seo")
        geo = latest.get("geo")
        comm = latest.get("community")
        lines.append(f"  SEO: {f'score {seo[\"score\"]:.0%}, last {seo[\"scanned_at\"][:10]}' if seo and seo.get('score') is not None else ('last ' + seo['scanned_at'][:10] if seo else 'no data')}")
        lines.append(f"  GEO: {f'score {geo[\"score\"]}/100, last {geo[\"scanned_at\"][:10]}' if geo else 'no data'}")
        lines.append(f"  Community: {f'{comm[\"total_hits\"]} hits, last {comm[\"scanned_at\"][:10]}' if comm else 'no data'}")
        lines.append("")

    return "\n".join(lines)


def _handle_web(args: list[str]) -> None:
    """Handle /web command — start web dashboard."""
    try:
        from opencmo.web.app import run_server
    except ImportError:
        print("Web dashboard requires additional dependencies. Install with: pip install opencmo[web]")
        return

    port = 8080
    for i, a in enumerate(args):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    print(f"Starting web dashboard on http://localhost:{port}")
    run_server(port=port)


async def run_cli():
    print("=" * 60)
    print("  OpenCMO - Your AI Chief Marketing Officer")
    print("  Type a product URL and what you need, or 'quit' to exit.")
    print("  Commands: /monitor, /status, /web")
    print("=" * 60)
    print()

    input_items = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # Handle CLI commands
        if user_input.startswith("/"):
            try:
                parts = shlex.split(user_input)
            except ValueError:
                parts = user_input.split()

            cmd = parts[0].lower()

            if cmd == "/monitor":
                try:
                    result = await _handle_monitor(parts[1:])
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
                continue

            elif cmd == "/status":
                try:
                    result = await _handle_status()
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
                continue

            elif cmd == "/web":
                _handle_web(parts[1:])
                continue

            else:
                print(f"\nUnknown command: {cmd}. Available: /monitor, /status, /web\n")
                continue

        input_items.append({"role": "user", "content": user_input})

        print("\nCMO is working...\n")
        result = await Runner.run(cmo_agent, input_items)

        print(f"[{result.last_agent.name}]")
        print(result.final_output)
        print()

        input_items = result.to_input_list()
        # Truncate history to prevent context explosion with search/SEO/GEO reports
        MAX_HISTORY = 20
        if len(input_items) > MAX_HISTORY:
            input_items = input_items[:1] + input_items[-(MAX_HISTORY - 1):]


def main():
    load_dotenv()
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
