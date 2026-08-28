# Epic 1 (Foundation) — Tickets

Source: `docs/prds/asx-stock-tracker.md` (Epic 1) and
`docs/architecture/epic-1-foundation.md`.

Also tracked as GitHub issues, labeled `epic-1` (this file is the
archival copy, committed alongside the PRD and architecture doc).

Dependency order: **1 and 2 first (parallel-safe)** → 3, 5, 6 → 4 → 7 → 8.

---

## 1. Spike: confirm shared Ubuntu/WSL storage path

**Labels:** `epic-1`, `spike`

**Description:** The storage decision (SQLite as one shared local file)
assumes a partition/drive mounted by both native Ubuntu and WSL already
exists on this machine — unconfirmed. This is a hands-on check (or setup),
not code, and unblocks ticket 3.

**Acceptance criteria:**
- Confirm whether a partition/drive is currently mounted and writable from
  both native Ubuntu and WSL on this machine.
- If yes: document the exact path on each OS side (native Ubuntu path vs.
  the path WSL sees it at).
- If no: document what setting one up would take, and either do it or flag
  it as a blocker with a fallback recommendation.
- Write the findings into `docs/architecture/epic-1-foundation.md`'s "Open
  questions" section, replacing the mount-point open question.

**Dependencies:** none.
**Size:** S (a few hours).
**Verification:** `touch` a test file from native Ubuntu, confirm it's
visible from WSL at the documented path, and vice versa.

---

## 2. Project scaffold: uv packaging + layered module structure

**Labels:** `epic-1`

**Description:** Stand up the Python project per the architecture doc's
stack decision (Python + Textual + stdlib `sqlite3`, packaged with `uv`),
with the four-layer structure (core domain → storage → external
data-source seam → TUI presentation) so later epics have a home for their
code without restructuring.

**Acceptance criteria:**
- `uv`-managed project: `pyproject.toml` + lockfile, Textual as a
  dependency.
- Module layout reflecting the four layers, e.g.
  `finance_tracker/{domain,storage,datasource,tui}/`, each with a
  placeholder `__init__.py`.
- A console-script entry point (e.g. `finance-tracker`) that runs.
- README with the one-command dev setup (`uv sync`, `uv run
  finance-tracker`).
- Linter/formatter wired (e.g. `ruff`) — engineer's call on exact tool.

**Dependencies:** none.
**Size:** M (~half day).
**Verification:** fresh clone, `uv sync && uv run finance-tracker`
succeeds on both a native Ubuntu and a WSL terminal.

---

## 3. Data path resolution module

**Labels:** `epic-1`

**Description:** Implement the module that decides where the SQLite file
lives, per the architecture doc's explicit (never-guessed) precedence
order, plus the first-run WSL notice.

**Acceptance criteria:**
- Precedence implemented exactly: `FINANCE_TRACKER_DATA_DIR` env var →
  `~/.config/finance-tracker/config.toml` → XDG default
  (`~/.local/share/finance-tracker/`).
- Isolated in one module — nothing else in the codebase reads env/OS
  directly to find the data path.
- Running under WSL with no explicit override shows a first-run notice
  that the default is local-only and won't be seen from native Ubuntu,
  pointing at the shared path from ticket 1.
- Unit tests cover each precedence level and the WSL-notice branch.

**Dependencies:** 1 (real mount-point info for the notice text), 2
(scaffold to build in).
**Size:** M.
**Verification:** exercise each override method set/unset and confirm the
resolved path; run under WSL with nothing configured and confirm the
notice appears.

---

## 4. SQLite bootstrap: connection + schema_version + migration runner

**Labels:** `epic-1`

**Description:** Storage-layer foundation — opens/creates the SQLite file
at the resolved data path and provides a small migration runner keyed off
a `schema_version` table, so later epics add their own tables without a
heavier migration framework.

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
**Verification:** delete the local DB, run the app, confirm the file and
`schema_version` table are created; run again, confirm no duplicate work.

---

## 5. Price data API seam (stub interface for Epic 2)

**Labels:** `epic-1`

**Description:** Leave the boundary in place per the architecture doc so
Epic 2's price-fetch work doesn't require restructuring — a thin interface
in the `datasource` layer, no real implementation yet.

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

## 6. Minimal Textual TUI skeleton

**Labels:** `epic-1`

**Description:** A running Textual app with one placeholder screen,
proving the TUI stack works end-to-end on both native Ubuntu and WSL
terminals — no stock features yet.

**Acceptance criteria:**
- Textual `App` subclass with one screen showing static placeholder
  content (app name/version).
- Launched via the entry point from ticket 2.
- Renders correctly in both a native Ubuntu terminal and a WSL terminal.
- Basic keybinding works (e.g. `q` to quit).

**Dependencies:** 2.
**Size:** S/M.
**Verification:** run in both terminal environments, visually confirm
rendering and that quit works.

---

## 7. Wire the skeleton end-to-end

**Labels:** `epic-1`

**Description:** Connect TUI → domain → storage so the layers actually
talk to each other, not just exist side by side — e.g. the placeholder
screen displays the `schema_version` read through the storage module.

**Acceptance criteria:**
- TUI screen calls into the storage module (via the domain layer, even if
  currently a pass-through) and displays a real value from the DB.
- Confirms the full path: TUI → domain → storage → SQLite file at the
  resolved data path.
- No direct SQL or path-resolution calls from the TUI layer.

**Dependencies:** 4, 6.
**Size:** S.
**Verification:** run the app, confirm the displayed value matches the DB
file's actual contents (spot-check with the `sqlite3` CLI).

---

## 8. Epic 1 exit verification

**Labels:** `epic-1`

**Description:** Confirm the epic's actual goal — a shared data file
reachable from both OSes — is real, not aspirational, by running the
wired-up skeleton from both sides against the same file.

**Acceptance criteria:**
- Run the app from native Ubuntu, then from WSL, both pointed at the
  shared path from ticket 1.
- Write something identifiable from one side, read it back from the
  other — confirms both see the same DB state.
- Update `docs/architecture/epic-1-foundation.md`'s "Open questions" to
  close out anything resolved by tickets 1 and 3.
- Short sign-off note confirming Epic 1 is ready for Epic 2 to build on.

**Dependencies:** 1, 3, 4, 7.
**Size:** S (mostly manual verification + a small doc update).
**Verification:** the ticket's own steps are the verification for the
whole epic.
