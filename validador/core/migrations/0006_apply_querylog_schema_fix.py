from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_manual_rename_and_add_querylog_cols'),  # la que ya figura aplicada
    ]

    operations = [
        # Renombrar result -> status (si existiera 'result')
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='core_querylog' AND column_name='result'
                    ) THEN
                        ALTER TABLE core_querylog RENAME COLUMN result TO status;
                    END IF;
                END$$;
            """,
            reverse_sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='core_querylog' AND column_name='status'
                    ) THEN
                        ALTER TABLE core_querylog RENAME COLUMN status TO result;
                    END IF;
                END$$;
            """,
        ),
        # Agregar columnas (idempotente)
        migrations.RunSQL(
            sql="""
                ALTER TABLE core_querylog
                ADD COLUMN IF NOT EXISTS normalized varchar(240) DEFAULT '' NOT NULL,
                ADD COLUMN IF NOT EXISTS llm_reason text DEFAULT '' NOT NULL,
                ADD COLUMN IF NOT EXISTS result_json jsonb DEFAULT '{}'::jsonb NOT NULL,
                ADD COLUMN IF NOT EXISTS score double precision DEFAULT 0 NOT NULL,
                ADD COLUMN IF NOT EXISTS quality varchar(1) DEFAULT '' NOT NULL
            """,
            reverse_sql="""
                ALTER TABLE core_querylog
                DROP COLUMN IF EXISTS normalized,
                DROP COLUMN IF EXISTS llm_reason,
                DROP COLUMN IF EXISTS result_json,
                DROP COLUMN IF EXISTS score,
                DROP COLUMN IF EXISTS quality
            """,
        ),
    ]