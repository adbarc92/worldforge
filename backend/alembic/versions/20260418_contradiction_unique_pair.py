"""Dedupe and add unique constraint on contradiction chunk pair

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-18
"""
from alembic import op


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing duplicates: for each (project_id, normalized chunk pair), keep
    # the earliest-created record and delete the rest.
    op.execute(
        """
        DELETE FROM contradictions c1
        USING contradictions c2
        WHERE c1.project_id = c2.project_id
          AND LEAST(c1.chunk_a_id, c1.chunk_b_id) = LEAST(c2.chunk_a_id, c2.chunk_b_id)
          AND GREATEST(c1.chunk_a_id, c1.chunk_b_id) = GREATEST(c2.chunk_a_id, c2.chunk_b_id)
          AND (c1.created_at, c1.id) > (c2.created_at, c2.id)
        """
    )

    # Functional unique index — a normalized pair can only exist once per project.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_contradictions_pair
        ON contradictions (
            project_id,
            LEAST(chunk_a_id, chunk_b_id),
            GREATEST(chunk_a_id, chunk_b_id)
        )
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_contradictions_pair")
