"""add DataUpdate model

Revision ID: 61a7bd8921f4
Revises: f3f4ea54fc04
Create Date: 2024-10-29 11:30:42.017240

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "61a7bd8921f4"
down_revision: Union[str, None] = "f3f4ea54fc04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "data_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_count", sa.Integer(), nullable=False),
        sa.Column("domain_search_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_updates")),
    )
    op.execute(
        """
                INSERT INTO data_updates (created_at, updated_at, listing_count, domain_search_count)
                VALUES (
                    NOW(),
                    NOW(),
                    (SELECT COUNT(*) FROM listings WHERE auction_end_time < NOW()),
                    (SELECT COUNT(*) FROM domain_searches)
                );
               """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("data_updates")
    # ### end Alembic commands ###
