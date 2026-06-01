export type TableShape = "round" | "rectangular";

export interface TableCreate {
  number: number;
  name: string;
  shape: TableShape;
  capacity: number;
}

export interface Table {
  number: number;
  name: string;
  shape: TableShape;
  capacity: number;
  id: string;
  event_id: string;
  created_at: string;
  updated_at: string;
}

export interface GuestAtTable {
  id: string;
  full_name: string;
  guest_type: "adult" | "child";
  side: "groom" | "bride";
  confirmation_status: "pending" | "confirmed" | "rejected";
  has_accommodation: boolean;
  has_day_after: boolean;
  dietary_requirements: string;
  contact_info: string;
  position_index: number | null;
  table_id: string;
  invitation_id: string;
  created_at: string;
  updated_at: string;
}

export interface TableWithGuests extends Table {
  guests: GuestAtTable[];
}

export interface SeatingPosition {
  guest_id: string;
  position_index: number;
}

export const SHAPE_LABELS: Record<TableShape, string> = {
  round: "Okrągły",
  rectangular: "Prostokątny",
};