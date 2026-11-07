"""Create persistent state tables for native 2FUNC release."""

from sqlalchemy import inspect


STAGE_COUNT = 10


def run_migration(connection):
    """Create release-state schema and initialize the ten stage records."""
    connection.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS release_stage_state (
            stage_number INTEGER PRIMARY KEY
                CHECK (stage_number BETWEEN 1 AND 10),
            started_on TEXT,
            issued_amount TEXT NOT NULL DEFAULT '0'
        )
        """
    )

    connection.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS release_issuance_records (
            tx_id TEXT PRIMARY KEY,
            stage_number INTEGER NOT NULL,
            amount TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (stage_number)
                REFERENCES release_stage_state(stage_number)
        )
        """
    )

    inspector = inspect(connection)
    expected = {
        "release_stage_state": {
            "stage_number": "INTEGER",
            "started_on": "TEXT",
            "issued_amount": "TEXT",
        },
        "release_issuance_records": {
            "tx_id": "TEXT",
            "stage_number": "INTEGER",
            "amount": "TEXT",
            "recorded_at": "TEXT",
        },
    }

    for table, columns in expected.items():
        actual = {
            column["name"]: str(column["type"]).upper()
            for column in inspector.get_columns(table)
        }
        for column, expected_type in columns.items():
            actual_type = actual.get(column)
            if actual_type != expected_type:
                raise RuntimeError(
                    f"Incompatible schema: {table}.{column}; "
                    f"expected {expected_type}, found {actual_type}"
                )

    connection.exec_driver_sql(
        """
        INSERT OR IGNORE INTO release_stage_state
            (stage_number, started_on, issued_amount)
        VALUES
            (1, NULL, '0'),
            (2, NULL, '0'),
            (3, NULL, '0'),
            (4, NULL, '0'),
            (5, NULL, '0'),
            (6, NULL, '0'),
            (7, NULL, '0'),
            (8, NULL, '0'),
            (9, NULL, '0'),
            (10, NULL, '0')
        """
    )

    count = connection.exec_driver_sql(
        "SELECT COUNT(*) FROM release_stage_state"
    ).scalar_one()

    if count != STAGE_COUNT:
        raise RuntimeError(
            f"Expected exactly {STAGE_COUNT} release stages, found {count}"
        )

    print("2FUNC release-state schema and ten initial stages are ready.")
