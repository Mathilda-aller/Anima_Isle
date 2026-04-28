import logging

from sqlalchemy import inspect, text

from app.database import engine


logger = logging.getLogger(__name__)

LATEST_ALEMBIC_REVISION = "f8c1d7e4b2a9"


def ensure_sqlite_dev_schema_compatibility() -> None:
    """
    Keep the local SQLite test database compatible with the current models.

    Production uses MySQL + Alembic. Local SQLite databases in this repo can
    drift because older revisions are no longer present, which blocks Alembic
    upgrades entirely. For SQLite only, we patch the few known gaps and then
    stamp the revision marker to the latest head so local dev can proceed.
    """

    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)

    with engine.begin() as conn:
        ticket_columns = {column["name"] for column in inspector.get_columns("tickets")}
        if "selected_image_id" not in ticket_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN selected_image_id VARCHAR(128)"))
            logger.info("SQLite compat: added tickets.selected_image_id")
        if "updated_at" not in ticket_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN updated_at DATETIME"))
            logger.info("SQLite compat: added tickets.updated_at")
        conn.execute(
            text(
                """
                UPDATE tickets
                SET is_public = COALESCE(is_public, 0),
                    is_printed_intent = COALESCE(is_printed_intent, 0)
                """
            )
        )

        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "password_changed_at" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_changed_at DATETIME"))
            logger.info("SQLite compat: added users.password_changed_at")
        if "is_internal_tester" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_internal_tester BOOLEAN NOT NULL DEFAULT 0"))
            logger.info("SQLite compat: added users.is_internal_tester")

        existing_tables = set(inspector.get_table_names())

        if "password_reset_tokens" not in existing_tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE password_reset_tokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        user_id INTEGER NOT NULL,
                        token_hash VARCHAR(128) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        used_at DATETIME,
                        requested_ip VARCHAR(45),
                        user_agent VARCHAR(255),
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_id "
                    "ON password_reset_tokens (id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id "
                    "ON password_reset_tokens (user_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_password_reset_tokens_token_hash "
                    "ON password_reset_tokens (token_hash)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_expires_at "
                    "ON password_reset_tokens (expires_at)"
                )
            )
            logger.info("SQLite compat: created password_reset_tokens")

        if "email_verification_codes" not in existing_tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE email_verification_codes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        code_hash VARCHAR(128) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        used_at DATETIME,
                        send_count INTEGER NOT NULL,
                        requested_ip VARCHAR(45),
                        user_agent VARCHAR(255),
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_email_verification_codes_id "
                    "ON email_verification_codes (id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_email_verification_codes_email "
                    "ON email_verification_codes (email)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_email_verification_codes_code_hash "
                    "ON email_verification_codes (code_hash)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_email_verification_codes_expires_at "
                    "ON email_verification_codes (expires_at)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_email_verification_codes_created_at "
                    "ON email_verification_codes (created_at)"
                )
            )
            logger.info("SQLite compat: created email_verification_codes")

        if "ai_chat_logs" in existing_tables:
            conn.execute(text("UPDATE ai_chat_logs SET ai_risk_flag = COALESCE(ai_risk_flag, 0)"))

        if "alembic_version" in existing_tables:
            current_revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if current_revision != LATEST_ALEMBIC_REVISION:
                conn.execute(text("DELETE FROM alembic_version"))
                conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                    {"revision": LATEST_ALEMBIC_REVISION},
                )
                logger.info(
                    "SQLite compat: stamped alembic_version from %s to %s",
                    current_revision,
                    LATEST_ALEMBIC_REVISION,
                )
        else:
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            conn.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                {"revision": LATEST_ALEMBIC_REVISION},
            )
            logger.info("SQLite compat: created alembic_version")
