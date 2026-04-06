"""Add resolution_note to contradictions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("contradictions", sa.Column("resolution_note", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("contradictions", "resolution_note")
