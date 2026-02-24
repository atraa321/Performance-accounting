"""add manual study leave pay table

Revision ID: 0003_manual_study_leave
Revises: 0002_audit_log
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_manual_study_leave'
down_revision = '0002_audit_log'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'raw_manual_study_leave_pay',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('row_no', sa.Integer(), nullable=True),
        sa.Column('sheet_name', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('raw_manual_study_leave_pay')
