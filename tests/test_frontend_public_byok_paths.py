import re
from pathlib import Path


def test_site_stats_is_frontend_public_byok_path() -> None:
    client_ts = Path("frontend/src/api/client.ts").read_text()
    public_paths_match = re.search(r"PUBLIC_BYOK_PATHS = new Set\(\[(.*?)\]\);", client_ts, re.S)

    assert public_paths_match is not None
    assert '"/site/stats"' in public_paths_match.group(1)
