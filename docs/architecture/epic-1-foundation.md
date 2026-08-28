# Architecture Decision Doc — Epic 1: Foundation
*(ASX Stock Tracker v1, per `docs/prds/asx-stock-tracker.md`)*

## Problem & goals
The PRD leaves three foundational calls open before any epic can start: the
language/TUI stack, a stack that won't paint us into a corner for the future
GTK/Qt GUI (Epic 8), and how the local data file is reached from both native
Ubuntu and WSL on the same machine. Epic 1's goal is to close those out and
stand up a minimal running skeleton — no stock features yet — that later
epics build on without re-litigating the foundation.

## Approaches considered

**Language/TUI stack** — narrowed to four options (Python, Go, Rust,
Node/TS), evaluated specifically against the PRD's stated GTK/Qt preference
for the future GUI:
- *Python* — Textual (best-in-class TUI: built-in sortable/filterable table,
  `textual-plotext` for charts) + PyGObject/PySide6, both first-tier GTK and
  Qt bindings.
- *Rust* — ratatui (excellent) + gtk-rs (mature) but Qt bindings (cxx-qt) are
  newer/rougher; steeper day-to-day iteration cost.
- *Go* — Bubble Tea (excellent) but GTK bindings are less polished and Qt
  bindings are effectively unmaintained — real friction expected at Epic 8.
- *Node/TS* — Ink is workable but thinner for tables/charts; natural GUI path
  is Electron, not GTK/Qt, which undercuts the PRD's WSLg rationale entirely.
- **Decision: Python.** Only stack where both target GUI toolkits are
  genuinely first-tier, and Textual best covers the TUI feature list.

**Local data storage** — three options evaluated:
- *SQLite (single file)* — stdlib-only, handles the relational shape
  (holdings × dividends × alerts) and Epic 4's sort/filter queries natively,
  one portable file.
- *Plain JSON file* — most readable/hand-editable, but filter/sort and
  schema evolution (dividends/alerts arriving in later epics) become
  hand-rolled work.
- *TinyDB* — JSON-backed query layer; a third-party dependency doing what
  `sqlite3` already does for free, less proven for data the user cares about
  not corrupting.
- **Decision: SQLite.** Confirmed with the user.

## Recommended approach
Python + Textual for the TUI. SQLite as a single portable file, at a path
that is **explicitly configured**, never guessed — because native Ubuntu and
WSL are separate OS filesystems with separate home directories, so any
default under `~` would silently create two disconnected databases, which is
the exact fragmentation the PRD exists to kill. Code is layered (core domain
logic → storage → external data-source seam → TUI presentation) so Epic 8's
GTK/Qt GUI can reuse everything except the presentation layer without a
rewrite.

## Key decisions
- **Stack:** Python, Textual, stdlib `sqlite3`.
- **Packaging:** `uv` (single tool for venv + deps + run). Reversible/low-risk
  choice — swapping to pip+venv or poetry later wouldn't touch the
  architecture, so this isn't gated on a spike.
- **Data path resolution order:** `FINANCE_TRACKER_DATA_DIR` env var →
  `~/.config/finance-tracker/config.toml` → XDG default
  (`~/.local/share/finance-tracker/`), with a first-run notice when running
  under WSL with no explicit override configured, since the default in that
  case is local-only and won't be seen from native Ubuntu.
- **Data model shape (conceptual, not final schema — real tables land in
  their owning epics):**
  - `Holding` — ASX code, quantity, cost basis/purchase price, purchase date.
  - `PriceSnapshot` — last fetched price, timestamp, live-vs-last-known flag
    (feeds the PRD's "market closed/API down" edge case).
  - `Dividend` — belongs to a `Holding`; amount, date.
  - `PriceAlert` — belongs to a `Holding`; threshold, direction, triggered
    state.
  - Relationships: `Holding` is the hub — 1:N into `Dividend` and
    `PriceAlert`, 1:N (history) into `PriceSnapshot`.
  - A `schema_version` table plus a small migration runner so each later epic
    adds its own tables without a heavier migration framework.
- **Boundaries & contracts:**
  - *Price data API* — isolated behind a thin seam in its own module; only
    the ASX code crosses this boundary (per PRD, holdings/quantities/values
    stay local). Real client and provider validation is Epic 2's job — Epic 1
    just leaves the seam in place so that spike doesn't require restructuring
    anything.
  - *Data path config* — isolated in one module so "where the data lives" is
    decoupled from storage/domain/TUI code; this is what makes the dual-boot
    split tractable.
  - No auth/secrets boundary needed for v1: unofficial Yahoo Finance endpoint
    needs no API key, single local user, no accounts.

## Missing pieces & spikes
- **Shared-partition spike (blocks the storage goal in practice):** whether a
  partition/drive mounted by both native Ubuntu and WSL already exists is
  unconfirmed. Needs a short hands-on check (or setup) before "shared
  storage" is real rather than aspirational — do this early in Epic 1, since
  everything else about the storage decision assumes it.
- **Price API spike** (already flagged in the PRD, belongs to Epic 2 not 1):
  validate the unofficial Yahoo Finance endpoint's reliability/coverage for
  `.AX` tickers before the real price-fetch service is built.
- **Domain-knowledge risk** (PRD-flagged): no finance background on the team,
  so gain/loss math needs a review pass before it ships; worth explicitly
  checking whether AU franking credits belong in the `Dividend` shape before
  Epic 6 locks the schema in.

## Open questions
- Exact mount points for the shared partition on each OS (depends on the
  spike above) — needed to write the first-run WSL notice's guidance text.
- Whether franking credits are in scope for dividend tracking, or explicitly
  deferred — affects `Dividend`'s shape, not urgent for Epic 1 itself.
