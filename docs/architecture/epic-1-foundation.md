# Architecture Decision Doc — Epic 1: Foundation
*(ASX Stock Tracker v1, per `docs/prds/asx-stock-tracker.md`)*

## Problem & goals
The PRD leaves three foundational calls open before any epic can start: the
language/TUI stack, a stack that won't paint us into a corner for the future
GTK/Qt GUI (Epic 8), and how the local data is stored and reached. Epic 1's
goal is to close those out and stand up a minimal running skeleton — no
stock features yet — that later epics build on without re-litigating the
foundation.

**Scope reduction (this revision):** native Ubuntu (the Hyper-V VM standing
in for it) is deferred to a later version so a working WSL-only version
ships first. Everything below — TUI, API server, SQLite file — runs inside
WSL alone for this version; there is no second environment to reach yet.
The API-server architecture is kept regardless (see "Sharing that storage"
below) because it's still the right foundation for the multi-user future
even with only one environment today.

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

**Sharing that storage between WSL and "native Ubuntu"** — the assumption
this doc originally shipped with (a bare-metal Ubuntu dual boot exists on
this machine, so the fix is just mounting the same partition twice) turned
out to be false: there is no dual boot. The follow-up plan was a **Hyper-V
VM running Ubuntu** standing in for "native Ubuntu," which changes the
sharing problem from "two OSes mounting one physical disk" to "two separate
guest OSes on one Windows host" — ruling out a directly dual-mounted
partition and putting any file-sharing option (SMB, NFS) into SQLite's own
documented danger zone (it explicitly warns against network filesystems for
locking correctness).

**Scope reduction (this revision):** the Hyper-V VM is now deferred, so
there is only one environment (WSL) for this version — the cross-environment
sharing problem itself doesn't exist yet. Options evaluated below are kept
for the record and because the decision they led to (API server) is still
what's being built now, just serving one local client instead of several:
- *SMB share + app-level lock file* — moot without a second environment,
  and was already flagged as throwaway once multi-computer access is
  wanted, since a shared-file model doesn't extend to real multi-user.
- **Request-handling API server** — a single small server process is the
  *only* thing that ever opens the SQLite file. For this version it has
  exactly one client (the WSL TUI, over localhost), but the same boundary
  is what the VM and any future computer will become clients of later,
  and what the already-anticipated multi-user/multi-computer future needs
  a real boundary to build on.
- **Decision: request-handling API server, kept despite the reduced scope.**
  More upfront cost than the TUI opening SQLite directly would be for a
  single local environment, taken deliberately so this doesn't need a
  second migration when the VM and multi-user work return — building the
  throwaway direct-file version first was judged not worth it, same
  reasoning as before the scope reduction. Confirmed with the user.

## Recommended approach
Python + Textual for the TUI. SQLite as a single file, owned exclusively by
a request-handling API server — never opened directly by the TUI or any
other code. For this version, both the TUI and the server run locally
inside WSL; the TUI talks to the server over HTTP on localhost. Code is
layered (core domain logic → storage → external data-source seam → API
server/client → TUI presentation) so Epic 8's GTK/Qt GUI can reuse
everything except the presentation layer without a rewrite, and so both a
future native-Ubuntu/VM environment and a future multi-user version extend
the existing client/server boundary instead of replacing the storage model.

## Key decisions
- **Stack:** Python, Textual, stdlib `sqlite3`, FastAPI for the request-
  handling API.
- **Packaging:** `uv` (single tool for venv + deps + run). Reversible/low-risk
  choice — swapping to pip+venv or poetry later wouldn't touch the
  architecture, so this isn't gated on a spike.
- **Where the server lives (this version):** inside WSL, on localhost — the
  concerns that previously ruled WSL out (unstable IP across restarts, VM
  auto-shutdown after the last interactive session) applied to hosting a
  server that a *separate* environment needs to reach reliably. With only
  one environment for this version, they don't apply: the server only needs
  to be reachable by a client in the same WSL instance, started when the
  user starts working (via the `finance-tracker-server` entry point from
  ticket 2), not as an always-on background service. **This is expected to
  change again** when native Ubuntu/the VM returns — revisit "always-on,
  stable IP" hosting at that point rather than building it now for a
  client that doesn't exist yet.
- **Data path resolution order (server-side only):** `FINANCE_TRACKER_DATA_DIR`
  env var → `~/.config/finance-tracker/config.toml` → XDG default
  (`~/.local/share/finance-tracker/`), resolved once, in WSL, by the
  server process. No other code resolves a data path at all — the TUI only
  needs the server's URL (see ticket breakdown for that config's own
  precedence order).
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
  - *Request-handling API* — the storage layer (SQLite connection,
    migrations, domain operations) is only ever reachable through this
    server process; no other code anywhere opens the DB file directly. The
    TUI talks to a thin API-client module, never to storage or SQL directly
    — same rule Epic 8's future GUI will follow. This is what will make a
    future WSL/VM split (and later, multi-user) tractable without a locking
    hazard, once that split exists again.
  - *Price data API* — isolated behind a thin seam in its own module; only
    the ASX code crosses this boundary (per PRD, holdings/quantities/values
    stay local). Real client and provider validation is Epic 2's job — Epic 1
    just leaves the seam in place so that spike doesn't require restructuring
    anything.
  - *Data path config* — isolated in one module, used only by the server
    process, so "where the data lives" stays decoupled from storage/domain
    code.
  - No auth/secrets boundary needed for v1: unofficial Yahoo Finance endpoint
    needs no API key, single local user, no accounts. The request-handling
    API itself is unauthenticated for v1 too (single user, single trusted
    machine) — revisit when multi-user support is built.

## Missing pieces & spikes
- **Hyper-V VM setup — deferred, out of scope for this version.** No native
  Ubuntu exists on this machine (confirmed — no dual boot); building it
  (Windows edition is Pro, Hyper-V supported; Ubuntu install; systemd
  service; fixed IP) is real hands-on work, but it's no longer blocking
  Epic 1 since native Ubuntu itself was cut from this version's scope. Pick
  this back up, along with the WSL↔VM network reachability spike it
  contained, when native Ubuntu support returns.
- **Price API spike** (already flagged in the PRD, belongs to Epic 2 not 1):
  validate the unofficial Yahoo Finance endpoint's reliability/coverage for
  `.AX` tickers before the real price-fetch service is built.
- **Domain-knowledge risk** (PRD-flagged): no finance background on the team,
  so gain/loss math needs a review pass before it ships; worth explicitly
  checking whether AU franking credits belong in the `Dividend` shape before
  Epic 6 locks the schema in.

## Open questions
- Whether an External virtual switch (or WSL mirrored-networking mode) is
  needed to make the VM reachable from WSL — deferred along with the VM
  setup itself; revisit when native Ubuntu support returns.
- The future GUI epic's assumption that WSLg forwards GTK/Qt apps to the
  Windows desktop automatically **does not hold for a Hyper-V VM** — WSLg is
  WSL-specific plumbing. Whatever "native Ubuntu" ends up meaning for Epic 8
  (this VM, or something else by then) will need its own GUI-forwarding
  answer (RDP Enhanced Session Mode, X11 forwarding, or no forwarding at
  all). Not urgent now; flagged so Epic 8 planning doesn't inherit a wrong
  assumption from this doc.
- Whether franking credits are in scope for dividend tracking, or explicitly
  deferred — affects `Dividend`'s shape, not urgent for Epic 1 itself.
