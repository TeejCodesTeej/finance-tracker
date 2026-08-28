# PRD: ASX Stock Tracker (v1)

## Problem
Currently juggling multiple Excel spreadsheets that don't talk to each other to track investments and spending. This fragmentation directly contributes to overspending, since there's no unified view of finances. Evidence: personal, first-hand experience using the spreadsheets today.

## Goals
- Stop using the Excel spreadsheets entirely for stock tracking.
- See total ASX portfolio value at a glance, in one place.

Measured by: spreadsheet usage for stock tracking drops to zero, and portfolio value is visible from a single screen.

## Non-goals
- Budgeting tool — planned for a later version, after stock tracking ships in v1.
- Multi-user support — v1 is single-user; more users planned later.
- Native Windows 11 application — a future consideration, not v1.
- GUI application — planned for a later iteration, for native Ubuntu users. v1 ships as a TUI (terminal UI) application only.
- Cloud sync — nice-to-have for a later version; v1 is local-only.
- Importing existing spreadsheet data — a future feature, not v1.
- Investment advice features — explicitly excluded, so the app does not trigger financial-advice licensing requirements (e.g. AFSL in Australia).

## Users
**Primary:** the developer, as a single user for v1.
**Secondary:** none for v1 — more users are planned for a later version.
**Current workaround:** multiple Excel spreadsheets that don't sync with each other.

## Requirements
**Interface:** v1 ships as a TUI (terminal UI) application, usable on both native Ubuntu and WSL terminals. A GUI application for native Ubuntu is a later iteration (see Non-goals).

Core flow:
1. User manually enters an ASX code to add a stock holding (e.g. `BHP`).
2. App automatically pulls a live (delayed) price for that code from a market data API.
3. User views all holdings in a portfolio table that can be filtered and sorted.
4. For each holding and the portfolio as a whole, the app shows: current value, gain/loss, historical price charts, dividend tracking, and price alerts.

All of the above (manual entry, current value/gain-loss, historical charts, dividend tracking, price alerts) are must-have for v1 — no nice-to-have split within stock tracking itself.

## Edge cases & failure states
- **Market data API is down or the market is closed:** show a message that the market/data is unavailable, display the last successfully fetched price, and label it clearly as the last-known price (not live).
- **Invalid or unknown ASX code:** show an error stating the code was not found.

## Technical notes
- **Data storage:** SQLite, owned exclusively by a small request-handling API server (see `docs/architecture/epic-1-foundation.md`) rather than a file opened directly by each environment. The server runs as a persistent service in a Hyper-V Ubuntu VM (this machine's stand-in for "native Ubuntu" — no bare-metal dual boot exists); WSL and any other environment are HTTP clients of it. Chosen over a directly-shared file specifically because it also gives the later multi-computer/multi-user direction (see Non-goals) a client/server boundary to build on, instead of two throwaway architectures.
- **Price data source:** no ASX API is chosen yet. Recommended default: **Yahoo Finance (unofficial API, `.AX` ticker suffix)** — free, no API key, covers ASX, and provides historical data for the charts requirement in one source. It's unofficial and can break or get rate-limited without notice, so validate with a quick spike before building on it.
- **Data licensing:** delayed price data (not real-time) is acceptable, which avoids the need for a paid real-time ASX data license.
- **Data sent externally:** only the ASX code is sent to the price API. Holdings, quantities, and portfolio values stay local.
- **Regulatory:** no investment-advice features are planned, so standard financial-advice licensing (e.g. AFSL) is not expected to apply — kept explicit as a non-goal to preserve this.
- **Migration:** greenfield build — no existing schema or data to migrate for v1.
- **TUI framework:** no library chosen yet — see open questions.
- **Future GUI toolkit:** when the GUI iteration starts, prefer a standard Linux toolkit (e.g. GTK or Qt) so it runs under WSLg with little extra work later, since WSLg forwards standard Linux GUI apps to Windows automatically on Windows 11. Not a v1 decision.

## Priority
**Must-have (v1):**
- TUI interface, working on native Ubuntu and WSL terminals
- Manual ASX code entry
- Automatic (delayed) live price pull
- Current value & gain/loss per holding and total
- Historical price charts
- Dividend tracking
- Price alerts
- Filterable, sortable portfolio table
- Error handling for invalid codes and API/market downtime

**Nice-to-have (later versions):**
- GUI application for native Ubuntu (future WSLg support to be reassessed then)
- Budgeting tool
- Multi-user support
- Cloud sync
- Importing existing spreadsheet data
- Native Windows 11 application

## Risks & open questions
- **No finance domain knowledge:** risk of incorrect gain/loss calculations or misused terminology — may need extra review/validation of the numbers before shipping.
- **Data leak / privacy risk:** flagged as the top risk, particularly once multi-user support is added in a later version.
- **Which ASX price API to commit to:** recommended default is Yahoo Finance (`.AX` tickers), pending a short validation spike to confirm reliability and coverage.
- **Which TUI framework to use:** not yet chosen — needs a short evaluation before Epic 1 (Foundation) work begins.
- **Multi-user support (deferred):** when it's built, it should build on the API-server boundary established in Epic 1 (auth + per-user data scoping on top of the existing client/server split) rather than on a re-architecture — no concrete plan yet, flagged here so Epic 1's API-first choice isn't re-litigated from scratch later.

## Epics
Build order: Epics 1–4 are the critical path to a usable v1 (TUI app that can replace the spreadsheets). Epics 5–7 can follow in parallel or any order after. Epic 8 is a future iteration, started only after v1 ships.

1. **Foundation** — shared Ubuntu/WSL storage approach, TUI framework choice, app scaffold.
2. **ASX Price Data Integration** — API spike, price-fetch service, invalid-code and API-down handling.
3. **Holdings Management** — add/edit/remove a holding, persisted locally.
4. **Portfolio View (TUI)** — filterable/sortable holdings table, current value & gain/loss, total value.
5. **Historical Charts (TUI)** — historical price data + in-terminal chart rendering.
6. **Dividend Tracking** — record/display dividends per holding.
7. **Price Alerts** — set thresholds, trigger notifications.
8. **GUI Application (future iteration)** — GTK/Qt toolkit choice, native Ubuntu GUI covering Epics 3–7's feature set, WSLg validation.
