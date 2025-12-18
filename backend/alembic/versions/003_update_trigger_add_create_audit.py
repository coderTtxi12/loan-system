"""Update trigger to add CREATE audit job

Revision ID: 003_trigger_create_audit
Revises: 002_document_size
Create Date: 2024-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_trigger_create_audit'
down_revision = '002_document_size'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update notify_loan_change() function to create audit jobs for INSERT (CREATE) operations.
    
    This ensures all loan creation and status changes are audited via PostgreSQL triggers,
    eliminating duplicate audit jobs from Python code.
    """
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


def downgrade() -> None:
    """Revert to previous trigger function (only STATUS_CHANGE audit jobs)."""
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
            
            -- If status changed, also enqueue an audit job
            IF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
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

