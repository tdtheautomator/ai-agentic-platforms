"""
Initial database schema migration for banking-demo.

Creates loan_events and loan_applications tables for SQLite.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create initial schema: loan_events and loan_applications tables.
    """
    # Create loan_events table
    op.create_table(
        "loan_events",
        sa.Column("id", sa.String(8), primary_key=True),
        sa.Column("application_id", sa.String(50), nullable=False, index=True),
        sa.Column("session_num", sa.Integer(), nullable=False),
        sa.Column("agent", sa.String(50), nullable=False),
        sa.Column("event", sa.String(100), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("ts", sa.String(30), nullable=False),
    )

    # Create loan_applications table
    op.create_table(
        "loan_applications",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("customer_id", sa.String(50), nullable=False),
        sa.Column("customer_name", sa.String(100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, index=True),
        sa.Column("credit_score", sa.Integer(), nullable=False),
        sa.Column("annual_income", sa.Float(), nullable=False),
        sa.Column("created_at", sa.String(30), nullable=False),
        sa.Column("updated_at", sa.String(30), nullable=False),
    )


def downgrade() -> None:
    """
    Drop tables created in upgrade.
    """
    op.drop_table("loan_applications")
    op.drop_table("loan_events")
