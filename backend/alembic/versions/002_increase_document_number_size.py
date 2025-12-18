"""Increase document_number size for encryption

Revision ID: 002_document_size
Revises: 001_triggers
Create Date: 2025-12-12 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_document_size'
down_revision = '001_triggers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Increase document_number column size to accommodate encrypted PII.
    
    Fernet encryption produces base64-encoded tokens that can be 88+ characters,
    but the current column is only VARCHAR(50).
    """
    op.alter_column(
        'loan_applications',
        'document_number',
        existing_type=sa.String(50),
        type_=sa.String(255),
        existing_nullable=False,
        comment='Encrypted document number (PII) - increased for Fernet encryption',
    )


def downgrade() -> None:
    """Revert document_number column size back to 50."""
    op.alter_column(
        'loan_applications',
        'document_number',
        existing_type=sa.String(255),
        type_=sa.String(50),
        existing_nullable=False,
        comment='Encrypted document number (PII)',
    )
