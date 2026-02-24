"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-21 00:30:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_batch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.String(length=20), nullable=False),
        sa.Column("dept_name", sa.String(length=100), nullable=False),
        sa.Column("rule_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "rule_set",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "rule_param",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_set_id", sa.Integer(), nullable=False),
        sa.Column("param_key", sa.String(length=100), nullable=False),
        sa.Column("param_value", sa.String(length=100), nullable=False),
        sa.Column("param_value_num", sa.Numeric(12, 4), nullable=True),
        sa.Column("param_desc", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["rule_set_id"], ["rule_set.id"]),
    )

    op.create_table(
        "dict_item_mapping",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_item_name", sa.String(length=200), nullable=False),
        sa.Column("item_code", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "dict_item_behavior",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("behavior_type", sa.String(length=30), nullable=False),
    )

    op.create_table(
        "raw_hospital_perf_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("item_name_norm", sa.String(length=200), nullable=False),
        sa.Column("period_tag", sa.String(length=20), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_roster",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("perf_score", sa.Numeric(12, 2), nullable=False),
        sa.Column("eligible_for_surplus_weight", sa.Boolean(), nullable=True),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_night_shift",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("night_count", sa.Numeric(12, 2), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_reading_fee",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_doctor_workload",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("workload", sa.Numeric(12, 2), nullable=False),
        sa.Column("bed_days", sa.Numeric(12, 2), nullable=False),
        sa.Column("admission_cert_count", sa.Numeric(12, 2), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_nurse_workload",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Numeric(12, 2), nullable=False),
        sa.Column("blood_draw_count", sa.Numeric(12, 2), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_manual_doctor_workload_pay",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "raw_manual_pool_adjust",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("pool_code", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "dim_employee_month",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("role_type", sa.String(length=30), nullable=False),
        sa.Column("perf_score", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_director", sa.Boolean(), nullable=False),
        sa.Column("is_deputy_director", sa.Boolean(), nullable=False),
        sa.Column("is_head_nurse", sa.Boolean(), nullable=False),
        sa.Column("eligible_for_surplus_weight", sa.Boolean(), nullable=False),
        sa.Column("is_external", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "fact_pool",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("pool_code", sa.String(length=50), nullable=False),
        sa.Column("source_item_code", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "fact_pool_alloc",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("pool_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("weight", sa.Numeric(12, 4), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "fact_pay_detail",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("item_code", sa.String(length=50), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("source_item_code", sa.String(length=50), nullable=True),
        sa.Column("pay_type", sa.String(length=30), nullable=False),
        sa.Column("pool_code", sa.String(length=50), nullable=True),
        sa.Column("calc_note", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "fact_pay_summary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("direct_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("pool_nursing", sa.Numeric(12, 2), nullable=False),
        sa.Column("pool_doctor", sa.Numeric(12, 2), nullable=False),
        sa.Column("surplus", sa.Numeric(12, 2), nullable=False),
        sa.Column("grand_total", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "reconcile_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=50), nullable=False),
        sa.Column("source_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("delta", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )

    op.create_table(
        "qc_issue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("issue_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.Column("row_no", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run_batch.id"]),
    )


def downgrade() -> None:
    op.drop_table("qc_issue")
    op.drop_table("reconcile_item")
    op.drop_table("fact_pay_summary")
    op.drop_table("fact_pay_detail")
    op.drop_table("fact_pool_alloc")
    op.drop_table("fact_pool")
    op.drop_table("dim_employee_month")
    op.drop_table("raw_manual_pool_adjust")
    op.drop_table("raw_manual_doctor_workload_pay")
    op.drop_table("raw_nurse_workload")
    op.drop_table("raw_doctor_workload")
    op.drop_table("raw_reading_fee")
    op.drop_table("raw_night_shift")
    op.drop_table("raw_roster")
    op.drop_table("raw_hospital_perf_item")
    op.drop_table("dict_item_behavior")
    op.drop_table("dict_item_mapping")
    op.drop_table("rule_param")
    op.drop_table("rule_set")
    op.drop_table("run_batch")
