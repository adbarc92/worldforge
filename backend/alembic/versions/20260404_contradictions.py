"""Add contradictions table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contradictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_a_id", sa.String(36), nullable=False),
        sa.Column("chunk_b_id", sa.String(36), nullable=False),
        sa.Column("document_a_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_b_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_a_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("document_b_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("chunk_a_text", sa.Text(), nullable=False),
        sa.Column("chunk_b_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_contradictions_project_id", "contradictions", ["project_id"])


def downgrade():
    op.drop_index("ix_contradictions_project_id", table_name="contradictions")
    op.drop_table("contradictions")
