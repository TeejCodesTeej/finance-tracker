# Epic 1 (Foundation) — Tickets

Source: `docs/prds/asx-stock-tracker.md` (Epic 1) and
`docs/architecture/epic-1-foundation.md`.

Also tracked as GitHub issues, labeled `epic-1` (this file is the
archival copy, committed alongside the PRD and architecture doc).

**Revision note:** this epic's shape changed after ticket 1 turned up two
false assumptions — no native Ubuntu dual boot exists (a Hyper-V VM is
standing in for it), and a directly-shared SQLite file was replaced with a
request-handling API server (the VM runs the server; every environment,
including WSL, is a client). See the architecture doc's "Approaches
considered" for the reasoning. Tickets 3–4 shrank to server-side-only
concerns, and tickets 6–7 (new) — the API server and API client — didn't
exist in the original breakdown.

**Revision note 2 (scope reduction):** native Ubuntu/the Hyper-V VM is now
deferred to a later version, to get a working WSL-only version done first.
**Ticket 1 is deferred** and dropped out of this epic's dependency chain —
its VM setup and WSL↔VM networking spike return when native Ubuntu support
is picked back up. The API-server architecture is unchanged (see
architecture doc), it just has one local client (WSL) instead of several
for now: tickets 3, 4, 6, 7, 8, 9 and 10 are updated below to run
everything inside WSL rather than on the VM. Ticket numbering and the
GitHub issue
mapping are kept stable rather than renumbered.

Dependency order: **2 first** → 3, 5 → 4 → 6 → 7 → 8 → 9 → 10. (Ticket 1
deferred — no longer a dependency of anything in this list.)

**Ticket number ↔ GitHub issue number:** these no longer match 1:1 for
tickets 6–10. Issues #1–#5 were updated in place and kept their numbers;
#6–#8 were closed as superseded (their scope moved or got replaced); #9
went to the PR that made this revision. The new tickets landed on whatever
issue numbers came next:

| Ticket | GitHub issue |
|---|---|
| 1 | [#1](https://github.com/TeejCodesTeej/finance-tracker/issues/1) |
| 2 | [#2](https://github.com/TeejCodesTeej/finance-tracker/issues/2) |
| 3 | [#3](https://github.com/TeejCodesTeej/finance-tracker/issues/3) |
| 4 | [#4](https://github.com/TeejCodesTeej/finance-tracker/issues/4) |
| 5 | [#5](https://github.com/TeejCodesTeej/finance-tracker/issues/5) |
| 6 | [#10](https://github.com/TeejCodesTeej/finance-tracker/issues/10) |
| 7 | [#11](https://github.com/TeejCodesTeej/finance-tracker/issues/11) |
| 8 | [#12](https://github.com/TeejCodesTeej/finance-tracker/issues/12) |
| 9 | [#13](https://github.com/TeejCodesTeej/finance-tracker/issues/13) |
| 10 | [#14](https://github.com/TeejCodesTeej/finance-tracker/issues/14) |

---

## 1. Hyper-V Ubuntu VM: stand up + verify WSL reachability

**Status: deferred — out of scope for this version.** Native Ubuntu support
is cut from this version's scope (see revision note 2 above); this ticket
is not part of the current dependency chain and nothing else in this epic
depends on it anymore. Kept below, unmodified, as the plan to pick back up
when native Ubuntu support returns.

**Labels:** `epic-1`, `spike`, `blocked`, `deferred`

**Description:** No bare-metal Ubuntu dual boot exists on this machine —
confirmed. This ticket replaces the original "confirm the shared mount"
spike with the real setup work: build the Hyper-V VM that stands in for
"native Ubuntu," and confirm WSL can reach it over the network (needed
because the storage decision is now a request-handling API server hosted in
the VM — see architecture doc). This is hands-on setup, not code, and is
being **captured as a plan now, executed separately** rather than done
inside a planning session.

**Acceptance criteria:**
- Confirm Hyper-V is enabled on this Windows host (Pro edition, so
  supported; the feature/service appears to already be present based on
  how `Get-VM`/`Get-VMSwitch` failed — unauthorized rather than "not
  found" — but this needs an elevated check to be sure). Enable it if not.
- Create a Hyper-V VM, install Ubuntu, give it a static IP or a fixed DHCP
  reservation (the server needs a stable address).
- Confirm WSL can reach the VM's IP (default WSL NAT networking and a
  Hyper-V VM's default switch are separate private networks — this may
  need an External virtual switch, or WSL mirrored-networking mode, to
  bridge them). Document whichever fix was needed, if any.
- Write the findings into `docs/architecture/epic-1-foundation.md`'s "Open
  questions" section, replacing the networking open question.

**Dependencies:** none.
**Size:** M (VM + OS install + networking troubleshooting — larger than
the original spike estimate; do this outside a chat session).
**Verification:** from WSL, `curl`/`ping` the VM's IP on a test port and
get a response; from the VM, confirm it can see WSL isn't required (WSL is
a client only) but confirm the VM's own network config is stable across a
VM restart.

---

## 2. Project scaffold: uv packaging + layered module structure

**Labels:** `epic-1`

**Description:** Stand up the Python project per the architecture doc's
stack decision (Python + Textual + stdlib `sqlite3` + FastAPI, packaged
with `uv`), with the five-layer structure (core domain → storage →
external data-source seam → API server/client → TUI presentation) so later
epics have a home for their code without restructuring.

**Acceptance criteria:**
- `uv`-managed project: `pyproject.toml` + lockfile, Textual and FastAPI as
  dependencies.
- Module layout reflecting the five layers, e.g.
  `finance_tracker/{domain,storage,datasource,api,tui}/`, each with a
  placeholder `__init__.py`. `api/` holds both the server (ticket 6) and
  the client (ticket 7).
- A console-script entry point for the TUI (e.g. `finance-tracker`) and a
  separate one for the server (e.g. `finance-tracker-server`) that run.
- README with the one-command dev setup (`uv sync`, `uv run
  finance-tracker`, `uv run finance-tracker-server`).
- Linter/formatter wired (e.g. `ruff`) — engineer's call on exact tool.

**Dependencies:** none.
**Size:** M (~half day).
**Verification:** fresh clone, `uv sync` succeeds; both entry points run
(the server as a no-op stub is fine at this stage) on a WSL terminal.

---

## 3. Data path resolution module (server-side)

**Labels:** `epic-1`

**Description:** Implement the module that decides where the SQLite file
lives, per the architecture doc's explicit (never-guessed) precedence
order. This now runs **only inside the API server process**, which for
this version runs locally inside WSL — no other code resolves a data path,
since no other code touches the file. The original WSL first-run notice is
dropped: the TUI never has a local-only default to warn about anymore,
because it never resolves a data path at all.

**Acceptance criteria:**
- Precedence implemented exactly: `FINANCE_TRACKER_DATA_DIR` env var →
  `~/.config/finance-tracker/config.toml` → XDG default
  (`~/.local/share/finance-tracker/`).
- Isolated in one module — nothing else in the codebase reads env/OS
  directly to find the data path, and nothing outside the server process
  imports this module at all.
- Unit tests cover each precedence level.

**Dependencies:** 2 (scaffold to build in).
**Size:** S (shrank — no WSL-notice branch to build or test anymore).
**Verification:** exercise each override method set/unset and confirm the
resolved path.

---

## 4. SQLite bootstrap: connection + schema_version + migration runner

**Labels:** `epic-1`

**Description:** Storage-layer foundation — opens/creates the SQLite file
at the resolved data path and provides a small migration runner keyed off
a `schema_version` table, so later epics add their own tables without a
heavier migration framework. Lives entirely inside the API server process
(ticket 6), which for this version runs locally inside WSL — this module
is never imported by the TUI or any client.

**Acceptance criteria:**
- Opens/creates the SQLite file at the path from ticket 3.
- `schema_version` table created on first run.
- Migration runner applies any not-yet-applied migrations from an ordered
  list and bumps `schema_version`; idempotent on repeated runs.
- No feature tables yet — `Holding`/`Dividend`/etc. are explicitly out of
  scope; they land in their owning epics per the architecture doc.
- Unit tests: fresh DB initializes correctly; second run is a no-op; a
  fake migration applies and is recorded.

**Dependencies:** 2, 3.
**Size:** M.
**Verification:** in WSL, delete the local DB, run the server, confirm
the file and `schema_version` table are created; run again, confirm no
duplicate work.

---

## 5. Price data API seam (stub interface for Epic 2)

**Labels:** `epic-1`

**Description:** Leave the boundary in place per the architecture doc so
Epic 2's price-fetch work doesn't require restructuring — a thin interface
in the `datasource` layer, no real implementation yet. Unaffected by the
API-server change (it's a boundary the server's domain layer will call
into, not something clients reach directly).

**Acceptance criteria:**
- Interface module (e.g. `datasource/price_source.py`) defining the
  contract Epic 2 will implement: a `fetch_price(asx_code: str) ->
  PriceQuote`-shaped signature, with a placeholder `PriceQuote` type.
- A stub implementation (raises `NotImplementedError`, or returns canned
  data) so the rest of the app can wire against it before Epic 2 lands.
- Contract confirms only the ASX code crosses this boundary (per PRD:
  holdings/quantities/values stay local) — nothing else in the signature.

**Dependencies:** 2.
**Size:** S.
**Verification:** import and call the stub from a throwaway script/test,
confirm the interface shape is usable.

---

## 6. Request-handling API server

**Labels:** `epic-1`

**Description:** *(New — didn't exist in the original breakdown.)* The
server that is the sole owner of the SQLite file. For this version it
runs locally inside WSL, started via the `finance-tracker-server` entry
point (ticket 2) — not as an always-on background service (see
architecture doc's "Where the server lives" decision). Exposes domain
operations over HTTP (FastAPI); the storage layer (ticket 4) is only ever
called from inside this process.

**Acceptance criteria:**
- FastAPI app wired to the domain/storage layers from tickets 3–4.
- At least one real endpoint proving the full path works end-to-end (e.g.
  a health/version check that reads `schema_version` from the DB and
  returns it) — full domain endpoints (holdings, etc.) land in their
  owning epics.
- Starts via the `finance-tracker-server` entry point and stays up for
  the session; no systemd unit or boot-time autostart for this version —
  that returns when native Ubuntu/the VM does and a separate environment
  needs the server reachable without a user starting it by hand.
- Unauthenticated for v1 (single user, single trusted machine) — noted
  explicitly as a decision to revisit when multi-user support is built,
  not an oversight.

**Dependencies:** 2, 4.
**Size:** M.
**Verification:** in WSL, run the `finance-tracker-server` entry point,
`curl localhost:<port>/<health-path>` returns the expected value.

---

## 7. API client module

**Labels:** `epic-1`

**Description:** *(New.)* Thin HTTP client the TUI (and any future client)
uses to talk to the server from ticket 6. This is what "storage" means
from the TUI's point of view from now on — the TUI never imports the
storage or domain-DB modules directly.

**Acceptance criteria:**
- Client module wrapping HTTP calls to the server's endpoints (starting
  with whatever ticket 6 exposes).
- Server URL is itself configured, not guessed, mirroring ticket 3's
  pattern: `FINANCE_TRACKER_API_URL` env var → config file → a documented
  default (e.g. `http://localhost:<port>` for this version, since the
  server is always local — revisit the default once a non-local server,
  e.g. the VM, is a real target again).
- Isolated in one module — nothing else in the TUI layer makes raw HTTP
  calls to the server.

**Dependencies:** 2, 6 (needs at least one real endpoint to call against).
**Size:** S.
**Verification:** in WSL, call the client against the server running
locally, confirm the response matches what `curl` gets directly.

---

## 8. Minimal Textual TUI skeleton

**Labels:** `epic-1`

**Description:** A running Textual app with one placeholder screen,
proving the TUI stack works end-to-end on a WSL terminal — no stock
features yet.

**Acceptance criteria:**
- Textual `App` subclass with one screen showing static placeholder
  content (app name/version).
- Launched via the entry point from ticket 2.
- Renders correctly in a WSL terminal.
- Basic keybinding works (e.g. `q` to quit).

**Dependencies:** 2.
**Size:** S/M.
**Verification:** run in a WSL terminal, visually confirm rendering and
that quit works.

---

## 9. Wire the skeleton end-to-end

**Labels:** `epic-1`

**Description:** Connect TUI → API client → API server → domain → storage
so the layers actually talk to each other, not just exist side by side —
e.g. the placeholder screen displays the `schema_version` the server reads
through storage.

**Acceptance criteria:**
- TUI screen calls the API client (ticket 7), which calls the server
  (ticket 6), which reads a real value from the DB through storage (ticket
  4), and displays it.
- Confirms the full path: TUI → API client → HTTP → API server → domain →
  storage → SQLite file, all inside WSL.
- No direct storage, domain-DB, or raw-SQL calls from the TUI layer — only
  through the API client.

**Dependencies:** 6, 7, 8.
**Size:** S.
**Verification:** run the TUI and the server together in WSL, confirm the
displayed value matches the DB file's actual contents (spot-check with
the `sqlite3` CLI in WSL).

---

## 10. Epic 1 exit verification

**Labels:** `epic-1`

**Description:** Confirm the epic's actual goal for this reduced scope —
a working TUI-through-API-server-to-SQLite stack, running entirely inside
WSL, with a client/server boundary that later scope (native Ubuntu/the
VM, multi-user) can extend without a rewrite — is real, not aspirational.
The original cross-environment version of this ticket (TUI as a client
from both WSL and the VM against one server) is deferred along with
ticket 1; pick it back up when native Ubuntu support returns.

**Acceptance criteria:**
- Fresh clone in WSL: `uv sync`, start the server (ticket 6), run the TUI
  (ticket 8) against it, confirm the placeholder screen displays the real
  `schema_version` value read through the full stack (ticket 9).
- Restart the server and re-run the TUI — confirms state persists in the
  SQLite file rather than living only in memory.
- Confirm no code outside the API server process (ticket 6) imports
  storage or domain-DB modules directly — the TUI only ever goes through
  the API client (ticket 7).
- Update `docs/architecture/epic-1-foundation.md`'s "Open questions" to
  close out anything resolved by tickets 6–9, and confirm the VM-related
  open questions are still correctly marked deferred rather than resolved.
- Short sign-off note confirming Epic 1 is ready for Epic 2 to build on.

**Dependencies:** 6, 7, 9.
**Size:** S (mostly manual verification + a small doc update).
**Verification:** the ticket's own steps are the verification for the
whole epic.
