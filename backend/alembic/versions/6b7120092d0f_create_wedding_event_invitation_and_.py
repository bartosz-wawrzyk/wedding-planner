"""create wedding event, invitation, table and guest

Revision ID: 6b7120092d0f
Revises: a6054da936d9
Create Date: 2026-05-12 11:32:08.722726
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '6b7120092d0f'
down_revision: Union[str, Sequence[str], None] = 'a6054da936d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # =========================
    # EVENT
    # =========================
    op.create_table(
        'event',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('date_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ceremony_place', sa.String(length=255), nullable=True),
        sa.Column('ceremony_address', sa.String(length=500), nullable=True),
        sa.Column('reception_place', sa.String(length=255), nullable=True),
        sa.Column('reception_address', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['wp.user.id']),
        sa.PrimaryKeyConstraint('id'),

        schema='wp'
    )

    # =========================
    # INVITATION
    # =========================
    op.create_table(
        'invitation',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_id', sa.Uuid(), nullable=False),
        sa.Column('group_name', sa.String(length=255), nullable=False),
        sa.Column('status',sa.Enum('NOT_DELIVERED', 'DELIVERED', name='invitationstatus'),nullable=False,server_default='NOT_DELIVERED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['event_id'], ['wp.event.id']),

        sa.PrimaryKeyConstraint('id'),
        schema='wp'
    )

    # =========================
    # TABLE
    # =========================
    op.create_table(
        'table',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_id', sa.Uuid(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('shape', sa.Enum('ROUND', 'RECTANGULAR', name='tableshape'), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['event_id'], ['wp.event.id'], ondelete='CASCADE'),

        sa.PrimaryKeyConstraint('id'),

        sa.CheckConstraint('capacity > 0', name='check_table_capacity_positive'),
        sa.CheckConstraint('number > 0', name='check_table_number_positive'),

        schema='wp'
    )

    op.create_index(
        'ix_table_event_id',
        'table',
        ['event_id'],
        schema='wp'
    )

    # =========================
    # GUEST
    # =========================
    op.create_table(
        'guest',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_id', sa.Uuid(), nullable=False),
        sa.Column('invitation_id', sa.Uuid(), nullable=True),
        sa.Column('table_id', sa.Uuid(), nullable=True),
        sa.Column('position_index', sa.Integer(), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('guest_type', sa.Enum('ADULT', 'CHILD', name='guesttype'), nullable=False),
        sa.Column('side', sa.Enum('GROOM', 'BRIDE', name='guestside'), nullable=False),
        sa.Column('confirmation_status', sa.Enum('PENDING', 'CONFIRMED', 'REJECTED', name='confirmationstatus'), nullable=False),

        sa.Column('has_accommodation', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('has_day_after', sa.Boolean(), nullable=False, server_default=sa.text('false')),

        sa.Column('dietary_requirements', sa.Text(), nullable=True),
        sa.Column('contact_info', sa.String(length=255), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['event_id'], ['wp.event.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invitation_id'], ['wp.invitation.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['table_id'], ['wp.table.id'], ondelete='SET NULL'),

        sa.UniqueConstraint('table_id', 'position_index', name='uq_guest_table_position'),

        sa.CheckConstraint(
            "position_index IS NULL OR position_index >= 1",
            name="check_guest_position_positive",
        ),

        sa.PrimaryKeyConstraint('id'),

        schema='wp'
    )

    op.create_index(
        'ix_guest_event_id',
        'guest',
        ['event_id'],
        schema='wp'
    )

    op.create_index('ix_guest_table_id', 'guest', ['table_id'], schema='wp')
    op.create_index('ix_guest_invitation_id', 'guest', ['invitation_id'], schema='wp')


def downgrade() -> None:

    op.drop_index('ix_guest_invitation_id', table_name='guest', schema='wp')
    op.drop_index('ix_guest_table_id', table_name='guest', schema='wp')
    op.drop_index('ix_guest_event_id', table_name='guest', schema='wp')

    op.drop_table('guest', schema='wp')
    op.drop_table('table', schema='wp')
    op.drop_table('invitation', schema='wp')
    op.drop_table('event', schema='wp')

    sa.Enum(name='tableshape').drop(op.get_bind())