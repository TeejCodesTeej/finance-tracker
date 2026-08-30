"""Unit tests for the price data API seam (ticket 5)."""

import dataclasses
from datetime import UTC, datetime

import pytest

from finance_tracker.datasource.price_source import PriceQuote, StubPriceSource


def test_stub_fetch_price_raises_not_implemented() -> None:
    """Confirms the interface shape is usable: a caller can hold a
    `PriceSource` (here, the stub) and call `fetch_price(asx_code)` on it
    before Epic 2 lands a real implementation.
    """
    source = StubPriceSource()

    with pytest.raises(NotImplementedError):
        source.fetch_price("BHP")


def test_price_quote_only_takes_the_documented_fields() -> None:
    """`PriceQuote` exposes exactly the four documented fields, matching
    the contract that only the ASX code crosses the price-source boundary.
    """
    quote = PriceQuote(
        asx_code="BHP",
        price=45.67,
        as_of=datetime(2026, 8, 30, 10, 0, 0, tzinfo=UTC),
        is_live=True,
    )

    assert quote.asx_code == "BHP"
    assert quote.price == 45.67
    assert quote.as_of == datetime(2026, 8, 30, 10, 0, 0, tzinfo=UTC)
    assert quote.is_live is True


def test_price_quote_is_frozen() -> None:
    """Per the PRD, only the ASX code crosses the boundary — nothing about
    a `PriceQuote` should be mutable after the fact.
    """
    quote = PriceQuote(
        asx_code="BHP",
        price=45.67,
        as_of=datetime(2026, 8, 30, 10, 0, 0, tzinfo=UTC),
        is_live=True,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        quote.price = 99.99  # type: ignore[misc]
