from pydantic import BaseModel, ConfigDict

class EventStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_guests: int
    guests_confirmed: int
    guests_pending: int
    guests_rejected: int

    # Total amounts
    adults_total: int
    children_total: int
    bride_guests_total: int
    groom_guests_total: int

    # Details: CONFIRMED
    adults_confirmed: int
    children_confirmed: int
    bride_adults_confirmed: int
    bride_children_confirmed: int
    groom_adults_confirmed: int
    groom_children_confirmed: int

    # Details: PENDING
    adults_pending: int
    children_pending: int
    bride_adults_pending: int
    bride_children_pending: int
    groom_adults_pending: int
    groom_children_pending: int

    # Invitation statistics
    invitations_total: int
    invitations_bride: int
    invitations_groom: int

    # Accommodation
    accommodation_confirmed: int
    accommodation_pending: int