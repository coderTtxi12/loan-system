"""Initial database schema

Revision ID: 000_initial
Revises: 
Create Date: 2024-12-11 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create initial database schema with all tables.
    
    Creates:
    - users
    - loan_applications
    - loan_status_history
    - audit_logs
    - async_jobs
    - webhook_events
    """
    
    # Enable PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # Create enum types manually with IF NOT EXISTS to avoid conflicts
    # SQLAlchemy will try to create them when creating tables, so we create them first
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('ADMIN', 'ANALYST', 'VIEWER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE loan_status AS ENUM (
                'PENDING', 'VALIDATING', 'IN_REVIEW', 'APPROVED',
                'REJECTED', 'CANCELLED', 'DISBURSED', 'COMPLETED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_status AS ENUM (
                'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('ADMIN', 'ANALYST', 'VIEWER', name='user_role', create_type=False), nullable=False, server_default='VIEWER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create loan_applications table
    op.create_table(
        'loan_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('document_type', sa.String(20), nullable=False),
        sa.Column('document_number', sa.String(255), nullable=False, comment='Encrypted document number (PII) - increased for Fernet encryption'),
        sa.Column('document_hash', sa.String(64), nullable=False, comment='SHA256 hash for lookup without decryption'),
        sa.Column('full_name', sa.String(255), nullable=False, comment='Encrypted full name (PII)'),
        sa.Column('amount_requested', sa.Numeric(15, 2), nullable=False),
        sa.Column('monthly_income', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('status', postgresql.ENUM('PENDING', 'VALIDATING', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'CANCELLED', 'DISBURSED', 'COMPLETED', name='loan_status', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('risk_score', sa.Integer(), nullable=True, comment='Risk score 0-1000'),
        sa.Column('requires_review', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('banking_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Banking provider response (encrypted sensitive fields)'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Additional metadata and validation warnings'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_loan_applications_id', 'loan_applications', ['id'])
    op.create_index('ix_loan_applications_country_code', 'loan_applications', ['country_code'])
    op.create_index('ix_loan_applications_status', 'loan_applications', ['status'])
    op.create_index('ix_loan_applications_document_hash', 'loan_applications', ['document_hash'])
    op.create_index('idx_loans_country_status', 'loan_applications', ['country_code', 'status'])
    op.create_index('idx_loans_created_at', 'loan_applications', ['created_at'], postgresql_using='btree')
    op.create_index('idx_loans_pending_review', 'loan_applications', ['status', 'created_at'], 
                    postgresql_where=sa.text("status IN ('PENDING', 'IN_REVIEW')"))
    
    # Add CHECK constraints for loan_applications
    op.create_check_constraint(
        'valid_country',
        'loan_applications',
        sa.text("country_code IN ('ES', 'MX', 'CO', 'BR')")
    )
    op.create_check_constraint(
        'positive_amounts',
        'loan_applications',
        sa.text('amount_requested > 0 AND monthly_income >= 0')
    )
    
    # Create loan_status_history table
    op.create_table(
        'loan_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('loan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('previous_status', sa.String(30), nullable=True, comment='Previous status (null for initial creation)'),
        sa.Column('new_status', sa.String(30), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True, comment='User ID who made the change (null for system)'),
        sa.Column('reason', sa.Text(), nullable=True, comment='Reason for status change'),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional context data for the status change'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['loan_id'], ['loan_applications.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_loan_status_history_loan_id', 'loan_status_history', ['loan_id'])
    op.create_index('idx_status_history_loan_created', 'loan_status_history', ['loan_id', 'created_at'], postgresql_using='btree')
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False, comment='Type of entity: loan_application, user, etc.'),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(30), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True, comment='User or system ID that performed the action'),
        sa.Column('actor_type', sa.String(20), nullable=True, comment='USER, SYSTEM, WORKER, WEBHOOK'),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='JSON object with field changes: {field: {old: x, new: y}}'),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_entity_created', 'audit_logs', ['entity_type', 'entity_id', 'created_at'], postgresql_using='btree')
    op.create_index('idx_audit_actor_created', 'audit_logs', ['actor_id', 'created_at'], postgresql_using='btree')
    
    # Create async_jobs table
    op.create_table(
        'async_jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('queue_name', sa.String(50), nullable=False, comment='Queue name: risk_evaluation, audit, notifications, webhooks'),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Job payload data'),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='job_status', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0', comment='Higher priority = processed first'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error', sa.Text(), nullable=True, comment='Last error message if failed'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='When the job should be processed'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by', sa.String(100), nullable=True, comment='Worker ID that has locked this job'),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_async_jobs_queue_name', 'async_jobs', ['queue_name'])
    op.create_index('ix_async_jobs_status', 'async_jobs', ['status'])
    op.create_index('idx_jobs_pending_queue', 'async_jobs', ['queue_name', 'priority', 'scheduled_at'],
                    postgresql_where=sa.text("status = 'PENDING'"))
    op.create_index('idx_jobs_running', 'async_jobs', ['locked_by', 'locked_at'],
                    postgresql_where=sa.text("status = 'RUNNING'"))
    op.create_index('idx_jobs_completed', 'async_jobs', ['completed_at'],
                    postgresql_where=sa.text("status = 'COMPLETED'"))
    
    # Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source', sa.String(50), nullable=False, comment='Source of the webhook (banking provider name)'),
        sa.Column('event_type', sa.String(50), nullable=False, comment='Type of event (status_update, risk_score, etc.)'),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Full webhook payload'),
        sa.Column('signature', sa.String(256), nullable=True, comment='HMAC signature for verification'),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True, comment='Error message if processing failed'),
        sa.Column('loan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['loan_id'], ['loan_applications.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_webhook_events_source', 'webhook_events', ['source'])
    op.create_index('ix_webhook_events_event_type', 'webhook_events', ['event_type'])
    op.create_index('ix_webhook_events_processed', 'webhook_events', ['processed'])
    op.create_index('ix_webhook_events_loan_id', 'webhook_events', ['loan_id'])
    op.create_index('idx_webhook_unprocessed', 'webhook_events', ['processed', 'created_at'],
                    postgresql_where=sa.text('processed = false'))
    op.create_index('idx_webhook_source_type', 'webhook_events', ['source', 'event_type', 'created_at'])


def downgrade() -> None:
    """Drop all tables, constraints, enum types, and extensions."""
    op.drop_table('webhook_events')
    op.drop_table('async_jobs')
    op.drop_table('audit_logs')
    op.drop_table('loan_status_history')
    
    # Drop constraints before dropping table
    op.drop_constraint('positive_amounts', 'loan_applications', type_='check')
    op.drop_constraint('valid_country', 'loan_applications', type_='check')
    
    op.drop_table('loan_applications')
    op.drop_table('users')
    
    # Drop enum types (SQLAlchemy will drop them automatically when dropping tables,
    # but we do it explicitly to be safe)
    op.execute('DROP TYPE IF EXISTS job_status CASCADE')
    op.execute('DROP TYPE IF EXISTS loan_status CASCADE')
    op.execute('DROP TYPE IF EXISTS user_role CASCADE')
    
    # Note: Extensions are not dropped to avoid affecting other databases
