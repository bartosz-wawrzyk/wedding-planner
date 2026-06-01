import type { Guest } from "../guests/guests.types";

export interface InvitationCreate {
  group_name: string;
  guest_ids: string[];
  status?: "NOT_DELIVERED" | "DELIVERED";
}

export interface Invitation {
  group_name: string;
  id: string;
  event_id: string;
  guests: Guest[];
  status: "NOT_DELIVERED" | "DELIVERED";
  created_at: string;
  updated_at: string;
}