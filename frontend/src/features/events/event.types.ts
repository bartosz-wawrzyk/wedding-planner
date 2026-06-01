export interface EventCreate {
  name: string;
  date_time: string;
  ceremony_place: string;
  ceremony_address: string;
  reception_place: string;
  reception_address: string;
}

export interface Event extends EventCreate {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}