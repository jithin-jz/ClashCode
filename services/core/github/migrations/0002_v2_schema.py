"""
Migration from V1 schema to V2.

This migration is a NO-OP on fresh databases (0001_initial already has V2 schema).
It only applies changes on databases that were created with the original V1 0001_initial.
"""

from django.db import migrations, models


def upgrade_v1_to_v2(apps, schema_editor):
    """Upgrade V1 schema to V2 — only runs if old columns exist."""
    with schema_editor.connection.cursor() as cursor:
        columns = [
            col.name
            for col in schema_editor.connection.introspection.get_table_description(cursor, "github_githubconnection")
        ]

    # If access_token_encrypted already exists, this is a fresh V2 DB — skip
    if "access_token_encrypted" in columns:
        return

    # This is a V1 database — upgrade it
    vendor = schema_editor.connection.vendor

    if vendor == "postgresql":
        schema_editor.execute(
            "ALTER TABLE github_githubconnection RENAME COLUMN access_token TO access_token_encrypted"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubconnection ALTER COLUMN access_token_encrypted TYPE bytea USING access_token_encrypted::bytea"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubconnection ADD COLUMN IF NOT EXISTS repo_visibility varchar(10) DEFAULT 'public' NOT NULL"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubconnection ADD COLUMN IF NOT EXISTS include_problem_description boolean DEFAULT true NOT NULL"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubconnection ADD COLUMN IF NOT EXISTS consecutive_failures integer DEFAULT 0 NOT NULL"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubpushlog ADD COLUMN IF NOT EXISTS challenge_description text DEFAULT '' NOT NULL"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubpushlog ADD COLUMN IF NOT EXISTS commit_url varchar(200) DEFAULT '' NOT NULL"
        )
        schema_editor.execute(
            "ALTER TABLE github_githubpushlog ADD COLUMN IF NOT EXISTS started_at timestamp with time zone"
        )
        schema_editor.execute("ALTER TABLE github_githubpushlog ADD COLUMN IF NOT EXISTS duration_ms integer")
        schema_editor.execute("ALTER TABLE github_githubpushlog ALTER COLUMN status TYPE varchar(15)")
        schema_editor.execute(
            "CREATE INDEX IF NOT EXISTS github_conn_slug_idx ON github_githubpushlog (connection_id, challenge_slug)"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("github", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(upgrade_v1_to_v2, migrations.RunPython.noop),
    ]
