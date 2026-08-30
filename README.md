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

The TUI entry point is currently a placeholder:

```bash
uv run finance-tracker
```

The API server entry point is currently a placeholder:

```bash
uv run finance-tracker-server
```

The entry points currently print placeholder messages and exit. No HTTP server is started for now.

### Linting

```bash
uv run ruff check .
```
