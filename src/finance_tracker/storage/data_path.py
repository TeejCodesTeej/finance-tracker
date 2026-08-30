"""Data path resolution — decides where the SQLite file lives.

This is the *only* place in the codebase that reads the environment or the
filesystem to figure out where application data goes. It is only ever
imported from inside the API server process (see ticket 6/architecture
doc's "Sharing that storage" decision) — the TUI and any other client only
ever need the server's URL, never a data path.

Precedence, highest to lowest, resolved once at server startup:
1. ``FINANCE_TRACKER_DATA_DIR`` environment variable.
2. ``data_dir`` key in ``~/.config/finance-tracker/config.toml``.
3. XDG default: ``~/.local/share/finance-tracker/``.

Nothing is guessed: each level either yields a usable value or is skipped
in favor of the next.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path

ENV_VAR = "FINANCE_TRACKER_DATA_DIR"
CONFIG_RELATIVE_PATH = Path(".config") / "finance-tracker" / "config.toml"
XDG_RELATIVE_PATH = Path(".local") / "share" / "finance-tracker"


def resolve_data_dir(
    *, env: Mapping[str, str] | None = None, home: Path | None = None
) -> Path:
    """Resolve the directory the SQLite file lives in.

    ``env`` and ``home`` default to the real environment and the current
    user's home directory; tests pass fakes to exercise each precedence
    level without touching real state.
    """
    env = os.environ if env is None else env
    home = Path.home() if home is None else home

    env_value = env.get(ENV_VAR)
    if env_value:
        return Path(env_value).expanduser()

    config_value = _read_config_data_dir(home / CONFIG_RELATIVE_PATH)
    if config_value:
        return Path(config_value).expanduser()

    return home / XDG_RELATIVE_PATH


def _read_config_data_dir(config_file: Path) -> str | None:
    """Read the ``data_dir`` key from ``config_file``, if usable.

    Returns ``None`` (rather than raising) for a missing file, unreadable
    file, malformed TOML, or a missing/non-string ``data_dir`` key — any of
    which just falls through to the next precedence level.
    """
    if not config_file.is_file():
        return None

    try:
        with config_file.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError, OSError:
        return None

    value = data.get("data_dir")
    return value if isinstance(value, str) and value else None
