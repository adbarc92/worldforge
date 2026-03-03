"""add projects table and project_id to documents

Revision ID: a1b2c3d4e5f6
Revises: bf845c80b2c3
Create Date: 2026-03-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'bf845c80b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_PROJECT_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.execute(
        sa.text(
            "INSERT INTO projects (id, name, description, created_at, updated_at) "
            "VALUES (:id, :name, :desc, NOW(), NOW())"
        ).bindparams(id=DEFAULT_PROJECT_ID, name="Default", desc="Default project for existing documents")
    )

    op.add_column("documents", sa.Column("project_id", sa.String(36), nullable=True))

    op.execute(
        sa.text("UPDATE documents SET project_id = :pid").bindparams(pid=DEFAULT_PROJECT_ID)
    )

    op.alter_column("documents", "project_id", nullable=False)
    op.create_foreign_key("fk_documents_project_id", "documents", "projects", ["project_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_documents_project_id", "documents", type_="foreignkey")
    op.drop_column("documents", "project_id")
    op.drop_table("projects")
