"""add_optimized_event_guest_summary_view

Revision ID: 72e7797d2539
Revises: 6b7120092d0f
Create Date: 2026-05-28 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '72e7797d2539'
down_revision: Union[str, Sequence[str], None] = '6b7120092d0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW wp.event_guest_summary AS
        WITH invitation_counts AS (
            SELECT 
                i.event_id,
                COUNT(i.id) AS invitations_total,
                COUNT(DISTINCT i.id) FILTER (WHERE g.side = 'BRIDE') AS invitations_bride,
                COUNT(DISTINCT i.id) FILTER (WHERE g.side = 'GROOM') AS invitations_groom
            FROM wp.invitation i
            LEFT JOIN wp.guest g ON g.invitation_id = i.id
            GROUP BY i.event_id
        )
        SELECT
            g.event_id,
            COUNT(*) AS total_guests,
            
            -- Podział per status
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED') AS guests_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING') AS guests_pending,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'REJECTED') AS guests_rejected,
            
            -- Sumy globalne dla typów (potwierdzeni + oczekujący)
            COUNT(*) FILTER (WHERE g.confirmation_status IN ('CONFIRMED', 'PENDING') AND g.guest_type = 'ADULT') AS adults_total,
            COUNT(*) FILTER (WHERE g.confirmation_status IN ('CONFIRMED', 'PENDING') AND g.guest_type = 'CHILD') AS children_total,
            
            -- Podział na strony (potwierdzeni + oczekujący)
            COUNT(*) FILTER (WHERE g.confirmation_status IN ('CONFIRMED', 'PENDING') AND g.side = 'BRIDE') AS bride_guests_total,
            COUNT(*) FILTER (WHERE g.confirmation_status IN ('CONFIRMED', 'PENDING') AND g.side = 'GROOM') AS groom_guests_total,
            
            -- Szczegóły: POTWIERDZENI
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.guest_type = 'ADULT') AS adults_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.guest_type = 'CHILD') AS children_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.side = 'BRIDE' AND g.guest_type = 'ADULT') AS bride_adults_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.side = 'BRIDE' AND g.guest_type = 'CHILD') AS bride_children_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.side = 'GROOM' AND g.guest_type = 'ADULT') AS groom_adults_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.side = 'GROOM' AND g.guest_type = 'CHILD') AS groom_children_confirmed,
            
            -- Szczegóły: OCZEKUJĄCY
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.guest_type = 'ADULT') AS adults_pending,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.guest_type = 'CHILD') AS children_pending,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.side = 'BRIDE' AND g.guest_type = 'ADULT') AS bride_adults_pending,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.side = 'BRIDE' AND g.guest_type = 'CHILD') AS bride_children_pending,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.side = 'GROOM' AND g.guest_type = 'ADULT') AS groom_adults_pending,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.side = 'GROOM' AND g.guest_type = 'CHILD') AS groom_children_pending,
            
            -- Statystyki zaproszeń z CTE
            COALESCE(ic.invitations_total, 0) AS invitations_total,
            COALESCE(ic.invitations_bride, 0) AS invitations_bride,
            COALESCE(ic.invitations_groom, 0) AS invitations_groom,
            
            -- Zakwaterowanie (zsumowane dla uproszczenia struktury UI)
            COUNT(*) FILTER (WHERE g.confirmation_status = 'CONFIRMED' AND g.has_accommodation = true) AS accommodation_confirmed,
            COUNT(*) FILTER (WHERE g.confirmation_status = 'PENDING' AND g.has_accommodation = true) AS accommodation_pending
            
        FROM wp.guest g
        LEFT JOIN invitation_counts ic ON ic.event_id = g.event_id
        GROUP BY g.event_id, ic.invitations_total, ic.invitations_bride, ic.invitations_groom;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS wp.event_guest_summary;")