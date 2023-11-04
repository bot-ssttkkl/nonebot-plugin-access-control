"""empty message

Revision ID: 6fbda6d1d8ee
Revises: 875c4dd8c271
Create Date: 2023-08-31 22:26:07.794707

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.

revision = "6fbda6d1d8ee"
down_revision = "875c4dd8c271"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table(
        "nonebot_plugin_access_control_rate_limit_rule", schema=None
    ) as batch_op:
        batch_op.drop_index(
            "ix_nonebot_plugin_access_control_rate_limit_rule_subject_service"
        )
        batch_op.create_index(
            "ix_ac_rate_limit_rule_subject_service",
            ["subject", "service"],
            unique=False,
        )
    with op.batch_alter_table(
        "nonebot_plugin_access_control_rate_limit_token", schema=None
    ) as batch_op:
        batch_op.drop_index("ix_nonebot_plugin_access_control_rate_limit_token_rule_id")
        batch_op.create_index(
            batch_op.f("ix_ac_rate_limit_token_rule_id"), ["rule_id"], unique=False
        )
        batch_op.add_column(
            sa.Column(
                "expire_time",
                sa.DateTime(),
                nullable=False,
                default=datetime.fromtimestamp(0),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "nonebot_plugin_access_control_rate_limit_rule", schema=None
    ) as batch_op:
        batch_op.drop_index("ix_ac_rate_limit_rule_subject_service")
        batch_op.create_index(
            "ix_nonebot_plugin_access_control_rate_limit_rule_subject_service",
            ["subject", "service"],
            unique=False,
        )
    with op.batch_alter_table(
        "nonebot_plugin_access_control_rate_limit_token", schema=None
    ) as batch_op:
        batch_op.drop_index("ix_ac_rate_limit_token_rule_id")
        batch_op.create_index(
            batch_op.f("ix_nonebot_plugin_access_control_rate_limit_token_rule_id"),
            ["rule_id"],
            unique=False,
        )
        batch_op.drop_column("expire_time")
