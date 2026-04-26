import argparse
import asyncio
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
CHAT_DIR = SCRIPT_DIR.parent
if str(CHAT_DIR) not in sys.path:
    sys.path.insert(0, str(CHAT_DIR))

from dynamo import dynamo_client

logger = logging.getLogger("chat_migration")
TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill legacy chat messages from PostgreSQL into DynamoDB.")
    parser.add_argument(
        "--legacy-db-url",
        default=os.getenv("LEGACY_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="Legacy PostgreSQL connection string.",
    )
    parser.add_argument(
        "--table",
        default=os.getenv("LEGACY_CHAT_TABLE", "chatmessage"),
        help="Legacy PostgreSQL chat table name.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("MIGRATION_BATCH_SIZE", "500")),
        help="Number of rows to fetch per batch.",
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=int(os.getenv("MIGRATION_START_ID", "0")),
        help="Resume migration from rows with id greater than this value.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=int(os.getenv("MIGRATION_MAX_ROWS", "0")),
        help="Optional cap on migrated rows for testing. 0 means no cap.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and log rows without writing to DynamoDB.",
    )
    return parser.parse_args()


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def load_asyncpg():
    try:
        import asyncpg
    except ImportError as exc:
        raise RuntimeError("asyncpg is required for migration. Install it with `pip install -r requirements-migrate.txt`.") from exc
    return asyncpg


def _normalize_timestamp(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _validate_table_name(table_name: str) -> str:
    if not TABLE_NAME_PATTERN.fullmatch(table_name):
        raise RuntimeError("Invalid legacy table name. Use a simple identifier like `chatmessage`.")
    return table_name


async def migrate():
    load_dotenv(CHAT_DIR / ".env", override=False)
    args = parse_args()

    if not args.legacy_db_url:
        raise RuntimeError("No legacy database URL provided. Set LEGACY_DATABASE_URL or pass --legacy-db-url.")

    table_name = _validate_table_name(args.table)
    asyncpg = await load_asyncpg()

    logger.info(
        "Starting legacy chat migration from table=%s batch_size=%s start_id=%s dry_run=%s",
        args.table,
        args.batch_size,
        args.start_id,
        args.dry_run,
    )

    await dynamo_client.create_table_if_not_exists()

    migrated = 0
    last_id = args.start_id

    connection = await asyncpg.connect(args.legacy_db_url)
    try:
        while True:
            rows = await connection.fetch(
                f"""
                SELECT id, room, user_id, username, avatar_url, message, timestamp, reactions
                FROM {table_name}
                WHERE id > $1
                ORDER BY id
                LIMIT $2
                """,
                last_id,
                args.batch_size,
            )

            if not rows:
                break

            for row in rows:
                last_id = row["id"]
                timestamp = _normalize_timestamp(row["timestamp"])
                if not timestamp:
                    logger.warning("Skipping row id=%s with empty timestamp", last_id)
                    continue

                if args.dry_run:
                    migrated += 1
                    if args.max_rows and migrated >= args.max_rows:
                        logger.info(
                            "Reached max row limit (%s). Last migrated id=%s",
                            args.max_rows,
                            last_id,
                        )
                        return
                    continue

                await dynamo_client.save_message(
                    room_id=row["room"],
                    sender=row["username"],
                    message=row["message"],
                    user_id=row["user_id"],
                    avatar_url=row["avatar_url"],
                    timestamp=timestamp,
                    reactions=row["reactions"] or {},
                    increment_activity=False,
                )
                migrated += 1

                if args.max_rows and migrated >= args.max_rows:
                    logger.info(
                        "Reached max row limit (%s). Last migrated id=%s",
                        args.max_rows,
                        last_id,
                    )
                    return

            logger.info("Migrated %s rows so far. Last id=%s", migrated, last_id)

        logger.info(
            "Migration complete. Total migrated rows=%s last_id=%s",
            migrated,
            last_id,
        )
    finally:
        await connection.close()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(migrate())
