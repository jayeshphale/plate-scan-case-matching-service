"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-04 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='staff'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)

    # 3. Cameras table
    op.create_table(
        'cameras',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('camera_id', sa.String(length=100), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('truck_identifier', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('camera_id')
    )
    op.create_index(op.f('ix_cameras_tenant_id'), 'cameras', ['tenant_id'], unique=False)

    # 4. Cases table
    op.create_table(
        'cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vin', sa.String(length=50), nullable=False),
        sa.Column('origin_tenant_id', sa.String(length=36), nullable=True),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('assigned_user_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending_claim'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['origin_tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cases_vin'), 'cases', ['vin'], unique=False)
    op.create_index(op.f('ix_cases_tenant_id'), 'cases', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_cases_status'), 'cases', ['status'], unique=False)
    op.create_index('ix_case_tenant_vin_status', 'cases', ['tenant_id', 'vin', 'status'], unique=False)
    op.create_index(
        'uq_tenant_active_vin',
        'cases',
        ['tenant_id', 'vin'],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'")
    )

    # 5. Scans table
    op.create_table(
        'scans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('camera_id', sa.String(length=100), nullable=False),
        sa.Column('plate', sa.String(length=20), nullable=False),
        sa.Column('vin', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scans_camera_id'), 'scans', ['camera_id'], unique=False)
    op.create_index(op.f('ix_scans_plate'), 'scans', ['plate'], unique=False)
    op.create_index(op.f('ix_scans_vin'), 'scans', ['vin'], unique=False)
    op.create_index(op.f('ix_scans_scanned_at'), 'scans', ['scanned_at'], unique=False)
    op.create_index('ix_scans_vin_scanned_at', 'scans', ['vin', 'scanned_at'], unique=False)


def downgrade() -> None:
    op.drop_table('scans')
    op.drop_table('cases')
    op.drop_table('cameras')
    op.drop_table('users')
    op.drop_table('tenants')
