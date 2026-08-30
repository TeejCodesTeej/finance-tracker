"""Price data API seam (ticket 5).

Leaves the boundary in place per the architecture doc so Epic 2's
price-fetch work (e.g. a Yahoo Finance client) can be built without
restructuring anything else. No real implementation lives here yet.

Per the PRD, only the ASX code crosses this boundary — holdings,
quantities, and portfolio values stay local and are never passed to a
price source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class PriceQuote:
    """A single price observation for an ASX-listed stock.

    Placeholder shape — Epic 2 owns the real provider and may refine this
    once the chosen data source's actual response shape is known.
    """

    asx_code: str
    price: float
    as_of: datetime
    is_live: bool
    """False when this is the last-known price shown per the PRD's
    market-closed/API-down edge case, rather than a fresh live quote."""


class PriceSource(Protocol):
    """Contract for fetching a live (delayed) price for an ASX code.

    Implementations land in Epic 2 (e.g. a Yahoo Finance client). Only
    `asx_code` crosses this boundary — no holdings, quantities, or
    portfolio values.
    """

    def fetch_price(self, asx_code: str) -> PriceQuote:
        """Fetch the current (possibly delayed) price for `asx_code`."""
        ...


class StubPriceSource:
    """Placeholder `PriceSource` so the rest of the app can wire against
    the seam before Epic 2 lands a real implementation.
    """

    def fetch_price(self, asx_code: str) -> PriceQuote:
        raise NotImplementedError(
            "Price data source not implemented yet — lands in Epic 2."
        )
