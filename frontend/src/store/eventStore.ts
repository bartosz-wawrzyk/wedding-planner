import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ActiveEvent {
  id: string;
  name: string;
}

interface EventStore {
  activeEvent: ActiveEvent | null;
  setActiveEvent: (event: ActiveEvent | null) => void;
  clearActiveEvent: () => void;
}

export const useEventStore = create<EventStore>()(
  persist(
    (set) => ({
      activeEvent: null,
      setActiveEvent: (event) => set({ activeEvent: event }),
      clearActiveEvent: () => set({ activeEvent: null }),
    }),
    {
      name: "active-event-storage",
    }
  )
);