"""In-memory native 2FUNC ledger using exact integer base units."""

from dataclasses import dataclass

from financial_core.blockchain.fee_policy import FeeQuote
from financial_core.interfaces.native_ledger import (
    DuplicateTransaction,
    Issuance,
    LedgerError,
)
from financial_core.twofunc.supply import (
    MAX_SUPPLY_BASE_UNITS,
    drika_to_base_units,
)


class InsufficientBalance(LedgerError):
    """The sender does not have enough available balance."""


@dataclass(frozen=True)
class Transfer:
    """Transfer amount is expressed in native base units."""

    tx_id: str
    sender: str
    recipient: str
    amount: int

    @classmethod
    def in_drika(
        cls,
        tx_id: str,
        sender: str,
        recipient: str,
        amount_drika: int,
    ) -> "Transfer":
        """Build a transfer from an exact whole-Drika amount."""
        return cls(
            tx_id=tx_id,
            sender=sender,
            recipient=recipient,
            amount=drika_to_base_units(amount_drika),
        )


@dataclass(frozen=True)
class FeePayment:
    """Auditable fee record associated with a successful transfer."""

    tx_id: str
    payer: str
    transfer_recipient: str
    fee_recipient: str
    operation_type: str
    resource_units: int
    fee_drika: int
    fee_base_units: int


class NativeLedger:
    """In-memory ledger primitive, not a persistent blockchain.

    Balances and transfers use integer native base units.
    This primitive does not mint coins or decide genesis allocations.
    """

    def __init__(self, initial_balances=None):
        balances = dict(initial_balances or {})

        for account, amount in balances.items():
            if not isinstance(account, str) or not account.strip():
                raise LedgerError(
                    "account identifiers must be non-empty strings"
                )
            if isinstance(amount, bool) or not isinstance(amount, int):
                raise LedgerError(
                    "balances must be integer base-unit amounts"
                )
            if amount < 0:
                raise LedgerError("balances cannot be negative")

        if sum(balances.values()) > MAX_SUPPLY_BASE_UNITS:
            raise LedgerError(
                "ledger balances exceed the maximum 2FUNC supply"
            )

        self._balances = balances
        # Initial balances count as already issued/genesis-allocated supply.
        self._issued_supply = sum(balances.values())
        self._transactions = {}
        self._issuances = {}
        self._fee_payments = {}

    @property
    def total_balances(self) -> int:
        """Total balances measured in native base units."""
        return sum(self._balances.values())

    @property
    def issued_supply(self) -> int:
        """Total issued supply in native base units, including genesis balances."""
        return self._issued_supply

    @property
    def remaining_supply(self) -> int:
        """Remaining issuable supply in native base units."""
        return MAX_SUPPLY_BASE_UNITS - self._issued_supply

    def issue_to(self, tx_id: str, recipient: str, amount: int) -> Issuance:
        """Issue native 2FUNC to an account under the global supply cap.

        Amount is expressed in integer base units. All validation completes
        before balances, supply, or issuance records are mutated.
        """
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise LedgerError("issuance transaction ID is required")

        if not isinstance(recipient, str) or not recipient.strip():
            raise LedgerError("issuance recipient is required")

        if isinstance(amount, bool) or not isinstance(amount, int):
            raise LedgerError("issuance amount must be an integer base-unit amount")

        if amount <= 0:
            raise LedgerError("issuance amount must be positive")

        if tx_id in self._transactions or tx_id in self._issuances:
            raise DuplicateTransaction("transaction ID has already been used")

        if amount > MAX_SUPPLY_BASE_UNITS - self._issued_supply:
            raise LedgerError("issuance would exceed the maximum 2FUNC supply")

        recipient_balance = self.balance_of(recipient)
        issuance = Issuance(tx_id=tx_id, recipient=recipient, amount=amount)

        # Atomic in-memory state transition after all validations succeed.
        self._balances[recipient] = recipient_balance + amount
        self._issued_supply += amount
        self._issuances[tx_id] = issuance

        return issuance

    def issuance_for(self, tx_id: str) -> Issuance | None:
        """Return the issuance record for a successful issuance."""
        return self._issuances.get(tx_id)

    def balance_of(self, account: str) -> int:
        """Return an account balance in native base units."""
        return self._balances.get(account, 0)

    def _validate_transfer(
        self,
        tx: Transfer,
        *,
        extra_debit: int = 0,
    ) -> tuple[int, int]:
        """Validate a transfer and return sender/recipient balances."""

        if not isinstance(tx, Transfer):
            raise LedgerError("expected a Transfer")

        if not isinstance(tx.tx_id, str) or not tx.tx_id.strip():
            raise LedgerError("transaction ID is required")

        if not isinstance(tx.sender, str) or not tx.sender.strip():
            raise LedgerError("sender is required")

        if not isinstance(tx.recipient, str) or not tx.recipient.strip():
            raise LedgerError("recipient is required")

        if tx.sender == tx.recipient:
            raise LedgerError("sender and recipient must differ")

        if isinstance(tx.amount, bool) or not isinstance(tx.amount, int):
            raise LedgerError(
                "amount must be an integer base-unit amount"
            )

        if tx.amount <= 0:
            raise LedgerError("amount must be positive")

        if tx.tx_id in self._transactions:
            raise DuplicateTransaction(
                "transaction ID has already been used"
            )

        if (
            isinstance(extra_debit, bool)
            or not isinstance(extra_debit, int)
            or extra_debit < 0
        ):
            raise LedgerError("extra debit must be a non-negative integer")

        sender_balance = self.balance_of(tx.sender)
        recipient_balance = self.balance_of(tx.recipient)

        if sender_balance < tx.amount + extra_debit:
            raise InsufficientBalance(
                "insufficient 2FUNC balance for transfer and fee"
            )

        if self.total_balances > MAX_SUPPLY_BASE_UNITS:
            raise LedgerError(
                "ledger balances exceed the maximum supply"
            )

        return sender_balance, recipient_balance

    def transfer(self, tx: Transfer) -> Transfer:
        """Execute a transfer without a network fee."""
        sender_balance, recipient_balance = self._validate_transfer(tx)

        # All validation completes before either balance is changed.
        self._balances[tx.sender] = sender_balance - tx.amount
        self._balances[tx.recipient] = recipient_balance + tx.amount
        self._transactions[tx.tx_id] = tx

        return tx

    def transfer_with_fee(
        self,
        tx: Transfer,
        *,
        fee_quote: FeeQuote,
        fee_recipient: str,
    ) -> Transfer:
        """Atomically transfer funds and pay the quoted network fee.

        The sender pays amount + fee. The transfer recipient receives amount,
        and the fee recipient receives the fee. No balance or transaction
        record changes unless all validation succeeds.

        The quote must be produced by the configured FeePolicy. This method
        verifies its type and exact Drika-to-base-unit conversion; the caller
        remains responsible for obtaining it from the intended policy.
        """

        if not isinstance(fee_quote, FeeQuote):
            raise LedgerError("expected a FeeQuote")

        if (
            not isinstance(fee_quote.operation_type, str)
            or not fee_quote.operation_type.strip()
        ):
            raise LedgerError("fee operation type is required")

        if (
            isinstance(fee_quote.resource_units, bool)
            or not isinstance(fee_quote.resource_units, int)
            or fee_quote.resource_units < 0
        ):
            raise LedgerError("fee resource units are invalid")

        if (
            isinstance(fee_quote.fee_drika, bool)
            or not isinstance(fee_quote.fee_drika, int)
            or fee_quote.fee_drika < 0
        ):
            raise LedgerError("fee Drika amount is invalid")

        expected_fee_base_units = drika_to_base_units(
            fee_quote.fee_drika
        )

        if (
            isinstance(fee_quote.fee_base_units, bool)
            or not isinstance(fee_quote.fee_base_units, int)
            or fee_quote.fee_base_units != expected_fee_base_units
        ):
            raise LedgerError(
                "fee base units do not match the exact Drika conversion"
            )

        if not isinstance(fee_recipient, str) or not fee_recipient.strip():
            raise LedgerError("fee recipient is required")

        if fee_recipient in (tx.sender, tx.recipient):
            raise LedgerError(
                "fee recipient must differ from sender and transfer recipient"
            )

        sender_balance, recipient_balance = self._validate_transfer(
            tx,
            extra_debit=fee_quote.fee_base_units,
        )

        fee_recipient_balance = self.balance_of(fee_recipient)

        # Prepare the audit record before mutating balances.
        payment = FeePayment(
            tx_id=tx.tx_id,
            payer=tx.sender,
            transfer_recipient=tx.recipient,
            fee_recipient=fee_recipient,
            operation_type=fee_quote.operation_type,
            resource_units=fee_quote.resource_units,
            fee_drika=fee_quote.fee_drika,
            fee_base_units=fee_quote.fee_base_units,
        )

        # Atomic in-memory state transition: all checks are complete.
        self._balances[tx.sender] = (
            sender_balance - tx.amount - fee_quote.fee_base_units
        )
        self._balances[tx.recipient] = recipient_balance + tx.amount
        self._balances[fee_recipient] = (
            fee_recipient_balance + fee_quote.fee_base_units
        )
        self._transactions[tx.tx_id] = tx
        self._fee_payments[tx.tx_id] = payment

        return tx

    def fee_payment_for(self, tx_id: str) -> FeePayment | None:
        """Return the fee audit record for a successful fee-paying transfer."""
        return self._fee_payments.get(tx_id)

    def transaction_exists(self, tx_id: str) -> bool:
        """Return whether an identifier was used for a transfer or issuance."""
        return tx_id in self._transactions or tx_id in self._issuances
