"""Accounting entry contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AccountingEntry:
    """
    Immutable accounting record.

    Accounting is separate from UVI value state.
    This contract does not mutate balances.
    """

    entry_id: str
    operation_id: str
    account_id: str
    entry_type: str
    amount: str
    unit: str
    direction: str
    description: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccountingEntryRequest:
    """Request to create an accounting entry."""

    entry_id: str
    operation_id: str
    account_id: str
    entry_type: str
    amount: str
    unit: str
    direction: str
    description: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccountingEntryResult:
    """Result of accounting entry preparation."""

    entry: AccountingEntry
    recorded: bool = False
    authority: str = "ACCOUNTING"
