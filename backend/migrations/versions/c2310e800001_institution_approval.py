"""Add synthetic institution approval evidence without changing existing records."""

import sqlalchemy as sa
from alembic import op

revision = "c2310e800001"
down_revision = "c2310e700001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "institution_approvals",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("institution_id", sa.Uuid(as_uuid=False), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("academic_year", sa.String(7), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("evidence_mode", sa.String(20), nullable=False),
        sa.Column("evidence_snapshot", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("institution_id", "academic_year"),
        sa.CheckConstraint("status IN ('APPROVED','SUSPENDED')"),
        sa.CheckConstraint("version >= 1"),
        sa.CheckConstraint("evidence_mode = 'DEMO_FIXTURE'"),
        sa.CheckConstraint(
            "status <> 'APPROVED' OR (evidence_snapshot IS NOT NULL AND reviewed_at IS NOT NULL)",
            name="approval_evidence_required",
        ),
    )
    op.create_index("ix_institution_approvals_institution_id", "institution_approvals", ["institution_id"])
    op.create_table(
        "institution_approval_events",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column(
            "approval_id", sa.Uuid(as_uuid=False), sa.ForeignKey("institution_approvals.id"), nullable=False
        ),
        sa.Column("actor_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("evidence_snapshot", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("approval_id", "version"),
        sa.CheckConstraint("status IN ('APPROVED','SUSPENDED')"),
        sa.CheckConstraint("version >= 1"),
    )
    op.create_index(
        "ix_institution_approval_events_approval_id", "institution_approval_events", ["approval_id"]
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT COUNT(*) FROM institution_approvals")):
        raise RuntimeError(
            "Approval history exists. Retain the schema and its evidence instead of dropping it."
        )
    op.drop_table("institution_approval_events")
    op.drop_table("institution_approvals")
