export type GuestType = "adult" | "child";
export type Side = "groom" | "bride";
export type ConfirmationStatus = "pending" | "confirmed" | "rejected";

export interface GuestCreate {
  full_name: string;
  guest_type: GuestType;
  side: Side;
  confirmation_status: ConfirmationStatus;
  has_accommodation: boolean;
  has_day_after: boolean;
  dietary_requirements: string;
  contact_info: string;
  invitation_id?: string;
}

export interface Guest extends GuestCreate {
  id: string;
  table_id?: string;
  created_at: string;
  updated_at: string;
}

export const GUEST_TYPE_LABELS: Record<GuestType, string> = {
  adult: "Dorosły",
  child: "Dziecko",
};

export const SIDE_LABELS: Record<Side, string> = {
  groom: "Pana Młodego",
  bride: "Panny Młodej",
};

export const CONFIRMATION_LABELS: Record<ConfirmationStatus, string> = {
  pending: "Oczekuje",
  confirmed: "Potwierdzony",
  rejected: "Odrzucony",
};