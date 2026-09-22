"""
DATABASE MIGRATIONS
===================
Automatic schema migration runner for SQLite and PostgreSQL.
"""

from __future__ import annotations

from peewee import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    PostgresqlDatabase,
    TextField,
)

from .models.accounts import (
    Client,
    SubscriptionDelivery,
)
from .models.market import (
    ProvisioningState,
    ScannerStrategyProfile,
)
from .models.portfolio import (
    Position,
    Trade,
)
from .models.signals import (
    PublishedSignalFollowUp,
    Signal,
    SignalDelivery,
    SignalDeskState,
    SignalRun,
)


def run_auto_migrations(real_db) -> None:
    """Run all schema and data migrations against real_db."""
    try:
        from playhouse.migrate import PostgresqlMigrator, SqliteMigrator, migrate

        is_postgres = isinstance(real_db, PostgresqlDatabase)
        migrator = PostgresqlMigrator(real_db) if is_postgres else SqliteMigrator(real_db)

        columns = [col.name for col in real_db.get_columns('position')]
        migrations = []
        if 'target_price_2' not in columns:
            migrations.append(migrator.add_column('position', 'target_price_2', FloatField(null=True)))
        if 'tp1_hit' not in columns:
            migrations.append(migrator.add_column('position', 'tp1_hit', BooleanField(default=False)))
        if 'entry_usd_rate' not in columns:
            migrations.append(migrator.add_column('position', 'entry_usd_rate', FloatField(null=True)))
        if 'signal_id' not in columns:
            migrations.append(migrator.add_column('position', 'signal_id', CharField(null=True)))

        trade_columns = [col.name for col in real_db.get_columns('trade')]
        if 'entry_usd_rate' not in trade_columns:
            migrations.append(migrator.add_column('trade', 'entry_usd_rate', FloatField(null=True)))
        if 'exit_usd_rate' not in trade_columns:
            migrations.append(migrator.add_column('trade', 'exit_usd_rate', FloatField(null=True)))
        if 'signal_id' not in trade_columns:
            migrations.append(migrator.add_column('trade', 'signal_id', CharField(null=True)))

        signal_run_columns = [col.name for col in real_db.get_columns('signalrun')]
        if 'run_key' not in signal_run_columns:
            migrations.append(migrator.add_column('signalrun', 'run_key', CharField(null=True)))

        signal_delivery_columns = [col.name for col in real_db.get_columns('signaldelivery')] if 'signaldelivery' in real_db.get_tables() else []
        if signal_delivery_columns:
            if 'service_tier' not in signal_delivery_columns:
                migrations.append(migrator.add_column('signaldelivery', 'service_tier', CharField(default="SIGNALS_ONLY")))
            if 'destination_type' not in signal_delivery_columns:
                migrations.append(migrator.add_column('signaldelivery', 'destination_type', CharField(default="PORTFOLIO")))
            if 'destination_id' not in signal_delivery_columns:
                migrations.append(migrator.add_column('signaldelivery', 'destination_id', CharField(null=True)))
            if 'destination_name' not in signal_delivery_columns:
                migrations.append(migrator.add_column('signaldelivery', 'destination_name', CharField(null=True)))
            if 'destination_chat_id' not in signal_delivery_columns:
                migrations.append(migrator.add_column('signaldelivery', 'destination_chat_id', CharField(null=True)))
            if 'latency_ms' not in signal_delivery_columns:
                migrations.append(migrator.add_column('signaldelivery', 'latency_ms', FloatField(null=True)))

        published_followup_columns = [col.name for col in real_db.get_columns('publishedsignalfollowup')] if 'publishedsignalfollowup' in real_db.get_tables() else []
        if published_followup_columns:
            if 'service_tier' not in published_followup_columns:
                migrations.append(migrator.add_column('publishedsignalfollowup', 'service_tier', CharField(default="SIGNALS_ONLY")))
            if 'destination_type' not in published_followup_columns:
                migrations.append(migrator.add_column('publishedsignalfollowup', 'destination_type', CharField(default="PORTFOLIO")))
            if 'destination_id' not in published_followup_columns:
                migrations.append(migrator.add_column('publishedsignalfollowup', 'destination_id', CharField(null=True)))
            if 'destination_name' not in published_followup_columns:
                migrations.append(migrator.add_column('publishedsignalfollowup', 'destination_name', CharField(null=True)))
            if 'destination_chat_id' not in published_followup_columns:
                migrations.append(migrator.add_column('publishedsignalfollowup', 'destination_chat_id', CharField(null=True)))

        # Expand Signal uniqueness to include source
        try:
            signal_indexes = real_db.get_indexes('signal')
            has_new_signal_unique = any(
                bool(idx.unique) and tuple(idx.columns or ()) == ('ticker', 'date', 'signal_type', 'source')
                for idx in signal_indexes
            )
            if not has_new_signal_unique:
                for idx in signal_indexes:
                    cols = tuple(idx.columns or ())
                    if bool(idx.unique) and cols == ('ticker', 'date', 'signal_type'):
                        real_db.execute_sql(f'DROP INDEX IF EXISTS "{idx.name}"')
                real_db.execute_sql(
                    'CREATE UNIQUE INDEX IF NOT EXISTS "signal_ticker_date_signal_type_source_uniq" '
                    'ON "signal" ("ticker", "date", "signal_type", "source")'
                )
        except Exception as e:
            print(f"Signal unique index migration error: {e}")

        scanner_profile_columns = [col.name for col in real_db.get_columns('scannerstrategyprofile')]
        if 'ready_at' not in scanner_profile_columns:
            migrations.append(migrator.add_column('scannerstrategyprofile', 'ready_at', DateTimeField(null=True)))
        if 'activated_at' not in scanner_profile_columns:
            migrations.append(migrator.add_column('scannerstrategyprofile', 'activated_at', DateTimeField(null=True)))
        if 'activation_count' not in scanner_profile_columns:
            migrations.append(migrator.add_column('scannerstrategyprofile', 'activation_count', IntegerField(default=0)))
        if 'activation_history_json' not in scanner_profile_columns:
            migrations.append(migrator.add_column('scannerstrategyprofile', 'activation_history_json', TextField(default="[]")))

        provisioning_columns = [col.name for col in real_db.get_columns('provisioningstate')]
        if 'backfill_universe_choice' not in provisioning_columns:
            migrations.append(migrator.add_column('provisioningstate', 'backfill_universe_choice', CharField(default="EGX30")))

        signal_desk_columns = [col.name for col in real_db.get_columns('signaldeskstate')] if 'signaldeskstate' in real_db.get_tables() else []
        if signal_desk_columns and 'manual_queue_json' not in signal_desk_columns:
            migrations.append(migrator.add_column('signaldeskstate', 'manual_queue_json', TextField(default="{}")))

        client_columns = [col.name for col in real_db.get_columns('client')] if 'client' in real_db.get_tables() else []
        if client_columns:
            if 'subscription_tier' not in client_columns:
                migrations.append(migrator.add_column('client', 'subscription_tier', CharField(default="SIGNALS_ONLY")))
            if 'telegram_chat_id' not in client_columns:
                migrations.append(migrator.add_column('client', 'telegram_chat_id', CharField(null=True)))
            if 'report_language' not in client_columns:
                migrations.append(migrator.add_column('client', 'report_language', CharField(default="EN")))
            if 'risk_profile' not in client_columns:
                migrations.append(migrator.add_column('client', 'risk_profile', CharField(default="BALANCED")))
            if 'default_currency' not in client_columns:
                migrations.append(migrator.add_column('client', 'default_currency', CharField(default="EGP")))
            if 'paid_until' not in client_columns:
                migrations.append(migrator.add_column('client', 'paid_until', DateField(null=True)))
            if 'notes' not in client_columns:
                migrations.append(migrator.add_column('client', 'notes', TextField(null=True)))
            if 'updated_at' not in client_columns:
                migrations.append(migrator.add_column('client', 'updated_at', DateTimeField(null=True)))
            if 'delivery_paused' not in client_columns:
                migrations.append(migrator.add_column('client', 'delivery_paused', BooleanField(default=False)))
            if 'delivery_fail_count' not in client_columns:
                migrations.append(migrator.add_column('client', 'delivery_fail_count', IntegerField(default=0)))

        if migrations:
            migrate(*migrations)
            print(f"Auto-migrated ({'Postgres' if is_postgres else 'SQLite'}): updated database schema.")

        try:
            if 'signaldelivery' in real_db.get_tables():
                real_db.execute_sql(
                    """
                    UPDATE signaldelivery
                    SET
                        destination_type = COALESCE(NULLIF(destination_type, ''), 'PORTFOLIO'),
                        destination_id = CAST(portfolio_id AS TEXT),
                        destination_name = COALESCE(
                            NULLIF(destination_name, ''),
                            (SELECT name FROM portfolio WHERE portfolio.id = signaldelivery.portfolio_id)
                        )
                    WHERE portfolio_id IS NOT NULL
                      AND (destination_id IS NULL OR destination_id = '')
                    """
                )
        except Exception as e:
            print(f"SignalDelivery destination backfill error: {e}")

        try:
            if 'publishedsignalfollowup' in real_db.get_tables() and 'signaldelivery' in real_db.get_tables():
                real_db.execute_sql(
                    """
                    UPDATE publishedsignalfollowup
                    SET
                        service_tier = COALESCE(
                            (SELECT service_tier FROM signaldelivery WHERE signaldelivery.id = publishedsignalfollowup.delivery_id),
                            service_tier
                        ),
                        destination_type = COALESCE(
                            NULLIF((SELECT destination_type FROM signaldelivery WHERE signaldelivery.id = publishedsignalfollowup.delivery_id), ''),
                            COALESCE(NULLIF(destination_type, ''), 'PORTFOLIO')
                        ),
                        destination_id = COALESCE(
                            (SELECT destination_id FROM signaldelivery WHERE signaldelivery.id = publishedsignalfollowup.delivery_id),
                            destination_id
                        ),
                        destination_name = COALESCE(
                            (SELECT destination_name FROM signaldelivery WHERE signaldelivery.id = publishedsignalfollowup.delivery_id),
                            destination_name
                        ),
                        destination_chat_id = COALESCE(
                            (SELECT destination_chat_id FROM signaldelivery WHERE signaldelivery.id = publishedsignalfollowup.delivery_id),
                            destination_chat_id
                        )
                    WHERE delivery_id IS NOT NULL
                      AND (destination_id IS NULL OR destination_id = '')
                    """
                )
        except Exception as e:
            print(f"PublishedSignalFollowUp destination backfill error: {e}")

        try:
            delivery_indexes = real_db.get_indexes('signaldelivery') if 'signaldelivery' in real_db.get_tables() else []
            for idx in delivery_indexes:
                if bool(idx.unique) and tuple(idx.columns or ()) == ('run_id', 'portfolio_id', 'channel'):
                    real_db.execute_sql(f'DROP INDEX IF EXISTS "{idx.name}"')
            has_destination_unique = any(
                bool(idx.unique) and tuple(idx.columns or ()) == ('run_id', 'channel', 'destination_type', 'destination_id')
                for idx in delivery_indexes
            )
            if not has_destination_unique:
                real_db.execute_sql(
                    'CREATE UNIQUE INDEX IF NOT EXISTS "signaldelivery_run_channel_destination_uniq" '
                    'ON "signaldelivery" ("run_id", "channel", "destination_type", "destination_id")'
                )
            real_db.execute_sql(
                'CREATE INDEX IF NOT EXISTS "signaldelivery_run_portfolio_channel_idx" '
                'ON "signaldelivery" ("run_id", "portfolio_id", "channel")'
            )
        except Exception as e:
            print(f"SignalDelivery destination index migration error: {e}")

        try:
            followup_indexes = real_db.get_indexes('publishedsignalfollowup') if 'publishedsignalfollowup' in real_db.get_tables() else []
            for idx in followup_indexes:
                if bool(idx.unique) and tuple(idx.columns or ()) == ('lifecycle_id', 'trigger_state'):
                    real_db.execute_sql(f'DROP INDEX IF EXISTS "{idx.name}"')
            has_followup_destination_unique = any(
                bool(idx.unique) and tuple(idx.columns or ()) == ('lifecycle_id', 'trigger_state', 'destination_type', 'destination_id')
                for idx in followup_indexes
            )
            if not has_followup_destination_unique:
                real_db.execute_sql(
                    'CREATE UNIQUE INDEX IF NOT EXISTS "publishedfollowup_lifecycle_trigger_destination_uniq" '
                    'ON "publishedsignalfollowup" ("lifecycle_id", "trigger_state", "destination_type", "destination_id")'
                )
        except Exception as e:
            print(f"PublishedSignalFollowUp destination index migration error: {e}")

        try:
            real_db.create_tables([SubscriptionDelivery], safe=True)
        except Exception as e:
            print(f"Subscription delivery table migration error: {e}")

        try:
            for run in SignalRun.select().where((SignalRun.run_key.is_null(True)) | (SignalRun.run_key == "")):
                run.run_key = f"{run.run_date.isoformat()}:{str(run.scan_type or 'DAILY').upper()}"
                run.save()
        except Exception as e:
            print(f"SignalRun run_key backfill error: {e}")

        try:
            existing_indexes = real_db.get_indexes('signalrun')
            for index_meta in existing_indexes:
                cols = tuple(index_meta.columns or ())
                if cols == ('run_date', 'scan_type') and index_meta.unique:
                    real_db.execute_sql(f'DROP INDEX IF EXISTS "{index_meta.name}"')
            has_run_key_unique = any(
                tuple(index_meta.columns or ()) == ('run_key',) and index_meta.unique
                for index_meta in real_db.get_indexes('signalrun')
            )
            if not has_run_key_unique:
                real_db.execute_sql('CREATE UNIQUE INDEX IF NOT EXISTS signalrun_run_key ON signalrun (run_key)')
        except Exception as e:
            print(f"SignalRun index migration error: {e}")
    except Exception as e:
        print(f"Auto-migration error: {e}")
