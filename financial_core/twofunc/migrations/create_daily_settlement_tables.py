

def run_migration(connection):
    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS daily_settlement_choices (
            user_id TEXT NOT NULL,
            operational_date TEXT NOT NULL,
            destination TEXT NOT NULL
                CHECK (destination IN (
                    'Drika', 'SHIR', 'ΣSHIR', '2FUNC', 'Drik'
                )),
            selected_at_utc TEXT NOT NULL,
            PRIMARY KEY (user_id, operational_date)
        )
    """)

    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS daily_settlement_intents (
            settlement_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            operational_date TEXT NOT NULL,
            destination TEXT NOT NULL
                CHECK (destination IN (
                    'Drika', 'SHIR', 'ΣSHIR', '2FUNC', 'Drik'
                )),
            status TEXT NOT NULL,
            trigger_reason TEXT NOT NULL,
            operation_id TEXT NOT NULL UNIQUE,
            created_at_utc TEXT NOT NULL,
            finalized_at_utc TEXT,
            source_amount TEXT,
            source_unit TEXT,
            destination_amount TEXT,
            reference_price TEXT,
            current_price TEXT,
            uvi_transaction_id TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE (user_id, operational_date)
        )
    """)



    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS daily_point_remainders (
            user_id TEXT NOT NULL,
            operational_date TEXT NOT NULL,
            remainder_points TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL,
            PRIMARY KEY (user_id, operational_date),
            CHECK (
                CAST(remainder_points AS NUMERIC) >= 0
                AND CAST(remainder_points AS NUMERIC) < 4
            )
        )
    """)
    connection.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS daily_point_settlements (
            user_id TEXT NOT NULL,
            operational_date TEXT NOT NULL,
            daily_points TEXT NOT NULL,
            carry_in_points TEXT NOT NULL,
            drika_amount TEXT NOT NULL,
            remainder_points TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            PRIMARY KEY (user_id, operational_date),
            CHECK (CAST(daily_points AS NUMERIC) >= 0),
            CHECK (
                CAST(carry_in_points AS NUMERIC) >= 0
                AND CAST(carry_in_points AS NUMERIC) < 4
            ),
            CHECK (CAST(drika_amount AS NUMERIC) >= 0),
            CHECK (
                CAST(remainder_points AS NUMERIC) >= 0
                AND CAST(remainder_points AS NUMERIC) < 4
            )
        )
    """)
