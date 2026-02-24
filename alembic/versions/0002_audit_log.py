"""add operation log table

Revision ID: 0002_audit_log
Revises: 0001_init
Create Date: 2026-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0002_audit_log'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'operation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=True),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('operation_name', sa.String(length=200), nullable=False),
        sa.Column('operator', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SUCCESS'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_operation_log_run_id', 'operation_log', ['run_id'])
    op.create_index('idx_operation_log_type', 'operation_log', ['operation_type'])
    op.create_index('idx_operation_log_created_at', 'operation_log', ['created_at'])


def downgrade():
    op.drop_index('idx_operation_log_created_at', table_name='operation_log')
    op.drop_index('idx_operation_log_type', table_name='operation_log')
    op.drop_index('idx_operation_log_run_id', table_name='operation_log')
    op.drop_table('operation_log')
