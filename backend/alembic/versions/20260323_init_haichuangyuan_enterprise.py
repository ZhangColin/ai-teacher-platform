"""init_haichuangyuan_enterprise

Revision ID: 20260323_init_hcy
Revises: ef3a319b300c
Create Date: 2026-03-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20260323_init_hcy'
down_revision: Union[str, Sequence[str], None] = 'ef3a319b300c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 使用UUID作为海创元企业的ID
    hcy_enterprise_id = 'ffb82ac9-9c23-481e-afb5-9e979e8024c3'

    # Step 1: 插入海创元企业（如果不存在）
    op.execute(f"""
        INSERT IGNORE INTO enterprises (id, name, code, status, balance_gratis, balance_paid, debt_points, created_at, updated_at)
        VALUES ('{hcy_enterprise_id}', '海创元', 'hcy', 'active', 10000, 0, 0, NOW(), NOW())
    """)

    # Step 2: 将所有属于默认企业或没有企业的用户更新到海创元企业
    op.execute(f"""
        UPDATE users
        SET enterprise_id = '{hcy_enterprise_id}'
        WHERE enterprise_id IS NULL
           OR enterprise_id = 'default-ent-001'
           OR NOT EXISTS (SELECT 1 FROM enterprises WHERE id = users.enterprise_id)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 回滚：将海创元用户移回默认企业
    op.execute("""
        UPDATE users
        SET enterprise_id = 'default-ent-001'
        WHERE enterprise_id = 'ffb82ac9-9c23-481e-afb5-9e979e8024c3'
    """)

    # 删除海创元企业
    op.execute("""
        DELETE FROM enterprises WHERE id = 'ffb82ac9-9c23-481e-afb5-9e979e8024c3'
    """)
