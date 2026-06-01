import api from "../../api/axios";
import type { Invitation, InvitationCreate } from "./invitations.types";


export const invitationsService = {
  getInvitations: async (eventId: string): Promise<Invitation[]> => {
    const response = await api.get<Invitation[]>(`/events/${eventId}/invitations/`);
    return response.data;
  },

  createInvitation: async (eventId: string, payload: InvitationCreate): Promise<Invitation> => {
    const response = await api.post<Invitation>(`/events/${eventId}/invitations/`, payload);
    return response.data;
  },

  updateInvitation: async (eventId: string, invitationId: string, payload: InvitationCreate): Promise<Invitation> => {
    const response = await api.patch<Invitation>(`/events/${eventId}/invitations/${invitationId}`, payload);
    return response.data;
  },

  updateStatus: async (eventId: string, invitationId: string, status: "NOT_DELIVERED" | "DELIVERED" | "NOT_SENT"): Promise<Invitation> => {
    const response = await api.patch<Invitation>(
      `/events/${eventId}/invitations/${invitationId}/status`,
      { status }
    );
    return response.data;
  },

  deleteInvitation: async (eventId: string, invitationId: string): Promise<void> => {
    await api.delete(`/events/${eventId}/invitations/${invitationId}`);
  }
};