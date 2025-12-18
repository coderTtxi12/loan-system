"""Add PostgreSQL triggers for LISTEN/NOTIFY

Revision ID: 001_triggers
Revises: 
Create Date: 2024-12-11 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_triggers'
down_revision = '000_initial'  # Depends on initial schema migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create PostgreSQL triggers for LISTEN/NOTIFY.
    
    This enables real-time event notifications when loan applications
    are created or updated, which are then broadcast via Socket.IO.
    """
    
    # Function to notify on loan changes
    op.execute("""
        CREATE OR REPLACE FUNCTION notify_loan_change()
        RETURNS TRIGGER AS $$
        DECLARE
            payload JSON;
        BEGIN
            -- Build JSON payload with loan change information
            payload = json_build_object(
                'operation', TG_OP,
                'loan_id', COALESCE(NEW.id::text, OLD.id::text),
                'country_code', COALESCE(NEW.country_code, OLD.country_code),
                'old_status', OLD.status,
                'new_status', NEW.status,
                'timestamp', NOW()
            );
            
            -- Send notification to channel 'loan_changes'
            PERFORM pg_notify('loan_changes', payload::text);
            
            -- Enqueue audit job for INSERT (CREATE) or UPDATE with status change
            IF TG_OP = 'INSERT' THEN
                INSERT INTO async_jobs (
                    queue_name,
                    payload,
                    status,
                    scheduled_at
                ) VALUES (
                    'audit',
                    json_build_object(
                        'entity_type', 'loan_application',
                        'entity_id', NEW.id::text,
                        'action', 'CREATE',
                        'old_status', NULL,
                        'new_status', NEW.status,
                        'timestamp', NOW()
                    ),
                    'PENDING',
                    NOW()
                );
            ELSIF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
                INSERT INTO async_jobs (
                    queue_name,
                    payload,
                    status,
                    scheduled_at
                ) VALUES (
                    'audit',
                    json_build_object(
                        'entity_type', 'loan_application',
                        'entity_id', NEW.id::text,
                        'action', 'STATUS_CHANGE',
                        'old_status', OLD.status,
                        'new_status', NEW.status,
                        'timestamp', NOW()
                    ),
                    'PENDING',
                    NOW()
                );
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Trigger for INSERT and UPDATE operations
    # Drop trigger first (separate command for asyncpg compatibility)
    op.execute("DROP TRIGGER IF EXISTS trigger_notify_loan_change ON loan_applications;")
    
    # Create trigger (separate command)
    op.execute("""
        CREATE TRIGGER trigger_notify_loan_change
            AFTER INSERT OR UPDATE ON loan_applications
            FOR EACH ROW
            EXECUTE FUNCTION notify_loan_change();
    """)
    
    # Function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Trigger for updated_at (if not exists)
    # Drop trigger first (separate command for asyncpg compatibility)
    op.execute("DROP TRIGGER IF EXISTS trigger_update_timestamp ON loan_applications;")
    
    # Create trigger (separate command)
    op.execute("""
        CREATE TRIGGER trigger_update_timestamp
            BEFORE UPDATE ON loan_applications
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at();
    """)


def downgrade() -> None:
    """Remove triggers and functions."""
    op.execute("DROP TRIGGER IF EXISTS trigger_notify_loan_change ON loan_applications;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_timestamp ON loan_applications;")
    op.execute("DROP FUNCTION IF EXISTS notify_loan_change();")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at();")
