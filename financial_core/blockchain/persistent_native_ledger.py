"""SQLite-backed persistent native 2FUNC ledger."""

import sqlite3

from financial_core.blockchain.native_ledger import (
    DuplicateTransaction,
    FeePayment,
    Issuance,
    LedgerError,
    NativeLedger,
    Transfer,
)


class SQLiteNativeLedger(NativeLedger):
    """Persistent NativeLedger with atomic SQLite state snapshots.

    The database is the durable source of truth for this ledger instance.
    Existing NativeLedger remains unchanged and available for in-memory use.
    """

    def __init__(self, db_path, initial_balances=None):
        if not isinstance(db_path, str) or not db_path.strip():
            raise LedgerError("a non-empty SQLite database path is required")

        self._db_path = db_path
        self._db = sqlite3.connect(db_path, timeout=30)
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

        initialized = self._db.execute(
            "SELECT value FROM ledger_meta WHERE key = 'initialized'"
        ).fetchone()

        if initialized:
            super().__init__()
            self._load_state()
        else:
            super().__init__(initial_balances)
            self._persist_state()

    def _create_schema(self):
        with self._db:
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS ledger_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ledger_balances (
                    account TEXT PRIMARY KEY,
                    amount TEXT NOT NULL CHECK (length(amount) > 0 AND amount NOT GLOB '*[^0-9]*')
                );

                CREATE TABLE IF NOT EXISTS ledger_transfers (
                    tx_id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    amount TEXT NOT NULL CHECK (length(amount) > 0 AND amount NOT GLOB '*[^0-9]*' AND ltrim(amount, '0') <> '')
                );

                CREATE TABLE IF NOT EXISTS ledger_issuances (
                    tx_id TEXT PRIMARY KEY,
                    recipient TEXT NOT NULL,
                    amount TEXT NOT NULL CHECK (length(amount) > 0 AND amount NOT GLOB '*[^0-9]*' AND ltrim(amount, '0') <> '')
                );

                CREATE TABLE IF NOT EXISTS ledger_fee_payments (
                    tx_id TEXT PRIMARY KEY,
                    payer TEXT NOT NULL,
                    transfer_recipient TEXT NOT NULL,
                    fee_recipient TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    resource_units INTEGER NOT NULL,
                    fee_drika TEXT NOT NULL CHECK (length(fee_drika) > 0 AND fee_drika NOT GLOB '*[^0-9]*'),
                    fee_base_units TEXT NOT NULL CHECK (length(fee_base_units) > 0 AND fee_base_units NOT GLOB '*[^0-9]*')
                );
                """
            )

        self._migrate_numeric_columns()

    def _migrate_numeric_columns(self):
        """Safely migrate monetary columns to exact decimal TEXT storage."""
        tables = {
            "ledger_balances": {
                "columns": ("account", "amount"),
                "numeric": ("amount",),
                "schema": """
                    CREATE TABLE {table} (
                        account TEXT PRIMARY KEY,
                        amount TEXT NOT NULL
                            CHECK (
                                length(amount) > 0
                                AND amount NOT GLOB '*[^0-9]*'
                            )
                    )
                """,
            },
            "ledger_transfers": {
                "columns": ("tx_id", "sender", "recipient", "amount"),
                "numeric": ("amount",),
                "schema": """
                    CREATE TABLE {table} (
                        tx_id TEXT PRIMARY KEY,
                        sender TEXT NOT NULL,
                        recipient TEXT NOT NULL,
                        amount TEXT NOT NULL
                            CHECK (
                                length(amount) > 0
                                AND amount NOT GLOB '*[^0-9]*'
                                AND ltrim(amount, '0') <> ''
                            )
                    )
                """,
            },
            "ledger_issuances": {
                "columns": ("tx_id", "recipient", "amount"),
                "numeric": ("amount",),
                "schema": """
                    CREATE TABLE {table} (
                        tx_id TEXT PRIMARY KEY,
                        recipient TEXT NOT NULL,
                        amount TEXT NOT NULL
                            CHECK (
                                length(amount) > 0
                                AND amount NOT GLOB '*[^0-9]*'
                                AND ltrim(amount, '0') <> ''
                            )
                    )
                """,
            },
            "ledger_fee_payments": {
                "columns": (
                    "tx_id", "payer", "transfer_recipient",
                    "fee_recipient", "operation_type", "resource_units",
                    "fee_drika", "fee_base_units",
                ),
                "numeric": ("fee_drika", "fee_base_units"),
                "schema": """
                    CREATE TABLE {table} (
                        tx_id TEXT PRIMARY KEY,
                        payer TEXT NOT NULL,
                        transfer_recipient TEXT NOT NULL,
                        fee_recipient TEXT NOT NULL,
                        operation_type TEXT NOT NULL,
                        resource_units INTEGER NOT NULL,
                        fee_drika TEXT NOT NULL
                            CHECK (
                                length(fee_drika) > 0
                                AND fee_drika NOT GLOB '*[^0-9]*'
                            ),
                        fee_base_units TEXT NOT NULL
                            CHECK (
                                length(fee_base_units) > 0
                                AND fee_base_units NOT GLOB '*[^0-9]*'
                            )
                    )
                """,
            },
        }

        with self._db:
            for table, spec in tables.items():
                info = self._db.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()

                declared_types = {
                    row[1]: row[2].upper()
                    for row in info
                }

                if not info:
                    raise LedgerError(
                        f"cannot migrate missing table: {table}"
                    )

                if all(
                    declared_types.get(column) == "TEXT"
                    for column in spec["numeric"]
                ):
                    continue

                temporary = f"{table}__exact_text_migration"

                self._db.execute(
                    f"DROP TABLE IF EXISTS {temporary}"
                )
                self._db.execute(
                    spec["schema"].format(table=temporary)
                )

                columns = spec["columns"]
                column_sql = ", ".join(columns)
                select_parts = [
                    f"CAST({column} AS TEXT)"
                    if column in spec["numeric"]
                    else column
                    for column in columns
                ]
                select_sql = ", ".join(select_parts)

                self._db.execute(
                    f"""
                    INSERT INTO {temporary} ({column_sql})
                    SELECT {select_sql} FROM {table}
                    """
                )

                self._db.execute(f"DROP TABLE {table}")
                self._db.execute(
                    f"ALTER TABLE {temporary} RENAME TO {table}"
                )

    def _load_state(self):
        from financial_core.blockchain.twofunc_supply import (
            MAX_SUPPLY_BASE_UNITS,
        )

        balances = {
            account: int(amount)
            for account, amount in self._db.execute(
                "SELECT account, amount FROM ledger_balances"
            )
        }

        issued_row = self._db.execute(
            "SELECT value FROM ledger_meta WHERE key = 'issued_supply'"
        ).fetchone()

        if not issued_row:
            raise LedgerError("persistent ledger has no issued-supply record")

        issued_supply = int(issued_row[0])

        if issued_supply < 0 or issued_supply > MAX_SUPPLY_BASE_UNITS:
            raise LedgerError("persistent issued supply is outside the supply cap")

        if sum(balances.values()) != issued_supply:
            raise LedgerError(
                "persistent balances do not match issued supply"
            )

        super().__init__(balances)
        self._issued_supply = issued_supply

        for tx_id, sender, recipient, amount in self._db.execute(
            "SELECT tx_id, sender, recipient, amount FROM ledger_transfers"
        ):
            self._transactions[tx_id] = Transfer(
                tx_id, sender, recipient, int(amount)
            )

        for tx_id, recipient, amount in self._db.execute(
            "SELECT tx_id, recipient, amount FROM ledger_issuances"
        ):
            self._issuances[tx_id] = Issuance(
                tx_id, recipient, int(amount)
            )

        for row in self._db.execute(
            """
            SELECT tx_id, payer, transfer_recipient, fee_recipient,
                   operation_type, resource_units, fee_drika, fee_base_units
            FROM ledger_fee_payments
            """
        ):
            tx_id, payer, recipient, fee_recipient, op, units, drika, base = row
            self._fee_payments[tx_id] = FeePayment(
                tx_id=tx_id,
                payer=payer,
                transfer_recipient=recipient,
                fee_recipient=fee_recipient,
                operation_type=op,
                resource_units=units,
                fee_drika=int(drika),
                fee_base_units=int(base),
            )

        transfer_ids = set(self._transactions)
        issuance_ids = set(self._issuances)

        if transfer_ids & issuance_ids:
            raise LedgerError(
                "persistent ledger reuses a transaction ID"
            )

        if set(self._fee_payments) - transfer_ids:
            raise LedgerError(
                "persistent fee record has no corresponding transfer"
            )

    def _persist_state(self):
        """Persist a complete state snapshot in one SQLite transaction."""
        with self._db:
            self._db.execute("DELETE FROM ledger_balances")
            self._db.execute("DELETE FROM ledger_transfers")
            self._db.execute("DELETE FROM ledger_issuances")
            self._db.execute("DELETE FROM ledger_fee_payments")

            self._db.executemany(
                "INSERT INTO ledger_balances(account, amount) VALUES (?, ?)",
                [(account, str(amount)) for account, amount in sorted(self._balances.items())],
            )

            self._db.executemany(
                """
                INSERT INTO ledger_transfers(tx_id, sender, recipient, amount)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (tx.tx_id, tx.sender, tx.recipient, str(tx.amount))
                    for tx in self._transactions.values()
                ],
            )

            self._db.executemany(
                """
                INSERT INTO ledger_issuances(tx_id, recipient, amount)
                VALUES (?, ?, ?)
                """,
                [
                    (item.tx_id, item.recipient, str(item.amount))
                    for item in self._issuances.values()
                ],
            )

            self._db.executemany(
                """
                INSERT INTO ledger_fee_payments(
                    tx_id, payer, transfer_recipient, fee_recipient,
                    operation_type, resource_units, fee_drika, fee_base_units
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.tx_id,
                        item.payer,
                        item.transfer_recipient,
                        item.fee_recipient,
                        item.operation_type,
                        item.resource_units,
                        item.fee_drika,
                        item.fee_base_units,
                    )
                    for item in self._fee_payments.values()
                ],
            )

            self._db.execute(
                """
                INSERT INTO ledger_meta(key, value)
                VALUES ('issued_supply', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(self._issued_supply),),
            )
            self._db.execute(
                """
                INSERT INTO ledger_meta(key, value)
                VALUES ('initialized', '1')
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """
            )

    def _snapshot_memory(self):
        return (
            self._balances.copy(),
            self._issued_supply,
            self._transactions.copy(),
            self._issuances.copy(),
            self._fee_payments.copy(),
        )

    def _restore_memory(self, snapshot):
        (
            self._balances,
            self._issued_supply,
            self._transactions,
            self._issuances,
            self._fee_payments,
        ) = snapshot

    def _run_persisted(self, operation, *args, **kwargs):
        """Refresh and persist a mutation under a SQLite write lock."""
        snapshot = self._snapshot_memory()
        try:
            # Serialize writers before reading the latest ledger state.
            self._db.execute("BEGIN IMMEDIATE")
            self._load_state()

            result = operation(*args, **kwargs)
            self._persist_state()
            return result
        except Exception:
            if self._db is not None and self._db.in_transaction:
                self._db.rollback()
            self._restore_memory(snapshot)
            raise

    def issue_to(self, tx_id: str, recipient: str, amount: int) -> Issuance:
        return self._run_persisted(
            super().issue_to, tx_id, recipient, amount
        )

    def _transfer_current_state(self, tx: Transfer) -> Transfer:
        if (
            isinstance(tx, Transfer)
            and isinstance(tx.tx_id, str)
            and tx.tx_id in self._issuances
        ):
            raise DuplicateTransaction(
                "transaction ID has already been used"
            )
        return super().transfer(tx)

    def transfer(self, tx: Transfer) -> Transfer:
        return self._run_persisted(self._transfer_current_state, tx)

    def _transfer_with_fee_current_state(
        self,
        tx: Transfer,
        *,
        fee_quote,
        fee_recipient: str,
    ) -> Transfer:
        if (
            isinstance(tx, Transfer)
            and isinstance(tx.tx_id, str)
            and tx.tx_id in self._issuances
        ):
            raise DuplicateTransaction(
                "transaction ID has already been used"
            )
        return super().transfer_with_fee(
            tx,
            fee_quote=fee_quote,
            fee_recipient=fee_recipient,
        )

    def transfer_with_fee(
        self,
        tx: Transfer,
        *,
        fee_quote,
        fee_recipient: str,
    ) -> Transfer:
        return self._run_persisted(
            self._transfer_with_fee_current_state,
            tx,
            fee_quote=fee_quote,
            fee_recipient=fee_recipient,
        )

    def close(self):
        if getattr(self, "_db", None) is not None:
            self._db.close()
            self._db = None

    def __enter__(self):
        if self._db is None:
            raise LedgerError("persistent ledger is closed")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
