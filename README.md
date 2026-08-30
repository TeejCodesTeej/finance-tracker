# finance-tracker

ASX stock tracker — a TUI application for tracking portfolio holdings,
value, gain/loss, dividends, and price alerts. See
`docs/prds/asx-stock-tracker.md` for the full product spec and
`docs/architecture/epic-1-foundation.md` for the architecture.

## Development

One-command setup, using [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
```

This creates `.venv` and installs all dependencies (and dev dependencies,
e.g. `ruff`) from `uv.lock`.

Run the TUI:

```bash
uv run finance-tracker
```

Run the API server (the sole owner of the SQLite file — see the
architecture doc's storage decision):

```bash
uv run finance-tracker-server
```

For this version, both run locally inside WSL; the TUI talks to the
server over HTTP on localhost.

### Linting

```bash
uv run ruff check .
```
