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

**Sharing that storage between WSL and "native Ubuntu"** — the assumption
this doc originally shipped with (a bare-metal Ubuntu dual boot exists on
this machine, so the fix is just mounting the same partition twice) turned
out to be false: there is no dual boot. The actual plan is a **Hyper-V VM
running Ubuntu** standing in for "native Ubuntu." That changes the sharing
problem from "two OSes mounting one physical disk" to "two separate guest
OSes on one Windows host," which rules out a directly dual-mounted
partition and puts any file-sharing option (SMB, NFS) into SQLite's own
documented danger zone: it explicitly warns against network filesystems for
locking correctness. Options evaluated:
- *SMB share + app-level lock file* — WSL and the VM both mount a Windows
  SMB share and open the SQLite file directly; a heartbeat lock file guards
  against two environments opening it at once (SQLite's own OS-level
  locking isn't trusted over SMB, so the guard is done at the app level).
  Workable, but only protects against the concurrent-open case by policy,
  not architecture — and it's throwaway once multi-computer access is
  wanted, since a shared-file model doesn't extend to real multi-user.
- **Request-handling API server** — a single small server process is the
  *only* thing that ever opens the SQLite file. Every environment (WSL, the
  VM, and any future computer) is a client of it over HTTP. This removes
  the network-filesystem locking risk entirely (only one process ever
  touches the file — no cross-process locking to get wrong) and gives the
  already-anticipated multi-user/multi-computer future a real boundary to
  build on instead of a second migration later.
- **Decision: request-handling API server.** More upfront scope than a
  shared file, taken deliberately because it dissolves the locking problem
  rather than working around it, and because multi-user support is already
  flagged as wanted later — building the throwaway file-sharing version
  first was judged not worth it. Confirmed with the user.

## Recommended approach
Python + Textual for the TUI. SQLite as a single file, owned exclusively by
a request-handling API server that runs as a persistent (systemd) service
inside the Hyper-V Ubuntu VM — never opened directly by WSL, the TUI, or any
other environment. Every environment talks to the server over HTTP. Code is
layered (core domain logic → storage → external data-source seam → API
server/client → TUI presentation) so Epic 8's GTK/Qt GUI can reuse
everything except the presentation layer without a rewrite, and so a future
multi-user version extends the existing client/server boundary instead of
replacing the storage model.

## Key decisions
- **Stack:** Python, Textual, stdlib `sqlite3`, FastAPI for the request-
  handling API.
- **Packaging:** `uv` (single tool for venv + deps + run). Reversible/low-risk
  choice — swapping to pip+venv or poetry later wouldn't touch the
  architecture, so this isn't gated on a spike.
- **Where the server lives:** the Hyper-V VM, not WSL — WSL's default NAT
  networking gives it an unstable IP (changes every restart, confirmed no
  `.wslconfig` mirrored-networking override is set on this machine) and its
  VM auto-shuts-down shortly after the last interactive session closes,
  neither of which is acceptable for something meant to be always-on. The
  VM behaves like a normal machine: static/reserved IP, systemd-managed
  service, stays up independent of any terminal being open.
- **Data path resolution order (server-side only):** `FINANCE_TRACKER_DATA_DIR`
  env var → `~/.config/finance-tracker/config.toml` → XDG default
  (`~/.local/share/finance-tracker/`), resolved once, on the VM, by the
  server process. No other environment resolves a data path at all — they
  only need the server's URL (see ticket breakdown for that config's own
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
    — same rule Epic 8's future GUI will follow. This is what makes the
    WSL/VM split (and later, multi-user) tractable without a locking hazard.
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
- **Hyper-V VM setup (blocks the storage goal in practice):** no native
  Ubuntu exists on this machine (confirmed — no dual boot). The VM itself
  needs to be built: Windows edition is Pro (Hyper-V supported) and the
  Hyper-V module/service appears to already be present (`Get-VM` failed on
  an authorization error, not "cmdlet not found" — inconclusive without
  elevated access, but suggestive), Ubuntu installed inside it, and the
  request-handling server set up as a systemd service with a fixed IP. This
  is genuine hands-on setup work, not a quick confirm — deliberately not
  done inside a chat session; captured here as the plan, to be executed and
  reported back on separately.
- **WSL ↔ Hyper-V VM network reachability (new spike, part of the VM
  setup):** unverified. WSL uses default NAT networking (confirmed: no
  `.wslconfig`, no mirrored-networking override), which is a different
  private network than whatever virtual switch the Hyper-V VM ends up on.
  Whether WSL can reach the VM's IP out of the box, or needs an External
  virtual switch (or WSL mirrored-networking mode) to bridge the two, needs
  hands-on confirmation once the VM exists — before Epic 1's exit
  verification (client TUI in WSL successfully calling the server in the
  VM) can pass.
- **Price API spike** (already flagged in the PRD, belongs to Epic 2 not 1):
  validate the unofficial Yahoo Finance endpoint's reliability/coverage for
  `.AX` tickers before the real price-fetch service is built.
- **Domain-knowledge risk** (PRD-flagged): no finance background on the team,
  so gain/loss math needs a review pass before it ships; worth explicitly
  checking whether AU franking credits belong in the `Dividend` shape before
  Epic 6 locks the schema in.

## Open questions
- Whether an External virtual switch (or WSL mirrored-networking mode) is
  needed to make the VM reachable from WSL — resolved once the VM setup
  spike above is done.
- The future GUI epic's assumption that WSLg forwards GTK/Qt apps to the
  Windows desktop automatically **does not hold for a Hyper-V VM** — WSLg is
  WSL-specific plumbing. Whatever "native Ubuntu" ends up meaning for Epic 8
  (this VM, or something else by then) will need its own GUI-forwarding
  answer (RDP Enhanced Session Mode, X11 forwarding, or no forwarding at
  all). Not urgent now; flagged so Epic 8 planning doesn't inherit a wrong
  assumption from this doc.
- Whether franking credits are in scope for dividend tracking, or explicitly
  deferred — affects `Dividend`'s shape, not urgent for Epic 1 itself.
