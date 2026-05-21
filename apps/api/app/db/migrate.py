"""Migrações leves (sem Alembic) para dev/portfólio."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def run_migrations(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS seniority VARCHAR(32);
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS is_remote BOOLEAN;
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE candidate_profiles
            ADD COLUMN IF NOT EXISTS label VARCHAR(128);
            """
        )
    )
    await conn.execute(
        text(
            """
            UPDATE candidate_profiles
            SET label = COALESCE(
                NULLIF(TRIM(label), ''),
                structured->>'name',
                source_filename,
                'Perfil ' || id::text
            )
            WHERE label IS NULL OR TRIM(label) = '';
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE candidate_profiles
            DROP CONSTRAINT IF EXISTS candidate_profiles_demo_user_id_key;
            """
        )
    )
    # Índice único legado do SQLAlchemy (unique=True em demo_user_id)  impede vários currículos.
    await conn.execute(
        text("DROP INDEX IF EXISTS ix_candidate_profiles_demo_user_id;"),
    )
    await conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_candidate_profiles_demo_user_id
            ON candidate_profiles (demo_user_id);
            """
        )
    )
    await conn.commit()
