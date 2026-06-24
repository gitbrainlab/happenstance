from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"

ENV_ALIASES = {
    "GOOGLE_API_KEY": "GOOGLE_PLACES_API_KEY",
}


def load_project_env(path: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs from a project .env file without overriding env."""
    env_path = path or DEFAULT_ENV_PATH
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _clean_value(value)
        if key and key not in os.environ:
            os.environ[key] = value

    for source, target in ENV_ALIASES.items():
        if source in os.environ and target not in os.environ:
            os.environ[target] = os.environ[source]


def _clean_value(value: str) -> str:
    cleaned = value.strip()
    if " #" in cleaned:
        cleaned = cleaned.split(" #", 1)[0].rstrip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1]
    return cleaned
