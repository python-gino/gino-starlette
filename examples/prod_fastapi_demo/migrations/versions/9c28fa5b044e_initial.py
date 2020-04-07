"""initial

Revision ID: 9c28fa5b044e
Revises:
Create Date: 2020-02-14 21:15:22.049240

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c28fa5b044e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prod_fastapi_demo_users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nickname", sa.Unicode(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("prod_fastapi_demo_users")
