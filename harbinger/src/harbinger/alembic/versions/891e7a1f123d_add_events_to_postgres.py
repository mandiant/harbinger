"""Add events to postgres

Revision ID: 891e7a1f123d
Revises: eac63cedd02c
Create Date: 2025-06-26 06:33:51.157226

"""

from alembic import op
from harbinger.models import (
    Domain,
    Password,
    Kerberos,
    Credential,
    Proxy,
    InputFile,
    Component,
    ProxyJob,
    File,
    Playbook,
    PlaybookStep,
    PlaybookStepModifier,
    C2Job,
    Host,
    Process,
    Label,
    LabeledItem,
    C2Server,
    C2ServerStatus,
    C2Implant,
    SituationalAwareness,
    Share,
    ShareFile,
    Highlight,
    Hash,
    ParseResult,
    SocksServer,
    Action,
    CertificateAuthority,
    CertificateTemplate,
    C2ServerType,
    C2ServerArguments,
    Suggestion,
)


# revision identifiers, used by Alembic.
revision = "891e7a1f123d"
down_revision = "eac63cedd02c"
branch_labels = None
depends_on = None


# PostgreSQL function to notify changes
NOTIFY_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION notify_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify with the table name and operation as the channel
    -- Channel name: table.operation (e.g., cookies.insert)
    PERFORM pg_notify(
        'events',
        json_build_object(
            'table_name', TG_TABLE_NAME,
            'operation', LOWER(TG_OP),
            'before', row_to_json(OLD),
            'after', row_to_json(NEW)
        )::text
    );
    RETURN CASE
        WHEN TG_OP = 'DELETE' THEN OLD  -- Return OLD for DELETE
        ELSE NEW                        -- Return NEW for INSERT/UPDATE
    END;
END;
$$ LANGUAGE plpgsql;
"""

# SQL to drop the function
DROP_NOTIFY_FUNCTION_SQL = "DROP FUNCTION IF EXISTS notify_changes() CASCADE;"


def get_trigger_statements_for_table(table_name):
    """Generates INSERT, UPDATE, DELETE trigger statements for a given table."""
    triggers = []
    # INSERT Trigger
    triggers.append(
        f"CREATE TRIGGER on_{table_name}_insert "
        f"AFTER INSERT ON {table_name} FOR EACH ROW EXECUTE FUNCTION notify_changes();"
    )
    # UPDATE Trigger
    triggers.append(
        f"CREATE TRIGGER on_{table_name}_update "
        f"AFTER UPDATE ON {table_name} FOR EACH ROW EXECUTE FUNCTION notify_changes();"
    )
    # DELETE Trigger
    triggers.append(
        f"CREATE TRIGGER on_{table_name}_delete "
        f"AFTER DELETE ON {table_name} FOR EACH ROW EXECUTE FUNCTION notify_changes();"
    )
    return triggers


def get_drop_trigger_statements_for_table(table_name):
    """Generates DROP TRIGGER statements for a given table."""
    drops = []
    drops.append(f"DROP TRIGGER IF EXISTS on_{table_name}_insert ON {table_name};")
    drops.append(f"DROP TRIGGER IF EXISTS on_{table_name}_update ON {table_name};")
    drops.append(f"DROP TRIGGER IF EXISTS on_{table_name}_delete ON {table_name};")
    return drops


def upgrade():
    op.execute(NOTIFY_FUNCTION_SQL)

    models_to_trigger = [
        Domain,
        Password,
        Kerberos,
        Credential,
        Proxy,
        ProxyJob,
        InputFile,
        Component,
        File,
        Playbook,
        PlaybookStep,
        PlaybookStepModifier,
        C2Job,
        Host,
        Process,
        Label,
        LabeledItem,
        C2Server,
        C2ServerStatus,
        C2Implant,
        SituationalAwareness,
        Share,
        ShareFile,
        Highlight,
        Hash,
        ParseResult,
        SocksServer,
        Action,
        CertificateAuthority,
        CertificateTemplate,
        C2ServerType,
        C2ServerArguments,
        Suggestion,
    ]
    table_names = [table.__tablename__ for table in models_to_trigger]

    for table_name in table_names:
        if table_name == "alembic_version":  # Skip alembic's internal table
            continue
        trigger_sqls = get_trigger_statements_for_table(table_name)
        for sql in trigger_sqls:
            op.execute(sql)


def downgrade():
    models_to_trigger = [
        Domain,
        Password,
        Kerberos,
        Credential,
        Proxy,
        ProxyJob,
        InputFile,
        Component,
        File,
        Playbook,
        PlaybookStep,
        PlaybookStepModifier,
        C2Job,
        Host,
        Process,
        Label,
        LabeledItem,
        C2Server,
        C2ServerStatus,
        C2Implant,
        SituationalAwareness,
        Share,
        ShareFile,
        Highlight,
        Hash,
        ParseResult,
        SocksServer,
        Action,
        CertificateAuthority,
        CertificateTemplate,
        C2ServerType,
        C2ServerArguments,
        Suggestion,
    ]
    table_names = [table.__tablename__ for table in models_to_trigger]

    for table_name in reversed(table_names):
        if table_name == "alembic_version":
            continue
        drop_trigger_sqls = get_drop_trigger_statements_for_table(table_name)
        for sql in drop_trigger_sqls:
            op.execute(sql)

    op.execute(DROP_NOTIFY_FUNCTION_SQL)
