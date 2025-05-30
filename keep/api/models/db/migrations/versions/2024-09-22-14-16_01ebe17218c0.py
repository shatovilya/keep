"""Topology applications

Revision ID: 01ebe17218c0
Revises: 493f217af6b6
Create Date: 2024-09-22 14:16:17.078591

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "01ebe17218c0"
down_revision = "493f217af6b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "topologyapplication",
        sa.Column("tenant_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "topologyserviceapplication",
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["topologyapplication.id"],
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["topologyservice.id"],
        ),
        sa.PrimaryKeyConstraint("service_id", "application_id"),
    )

    with op.batch_alter_table("topologyservice", schema=None) as batch_op:
        batch_op.drop_column("application")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("topologyservice", schema=None) as batch_op:
        batch_op.add_column(sa.Column("application", sa.VARCHAR(), nullable=True))

    op.drop_table("topologyserviceapplication")
    op.drop_table("topologyapplication")
    # ### end Alembic commands ###
