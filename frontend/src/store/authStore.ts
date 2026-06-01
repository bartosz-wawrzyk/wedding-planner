import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  role: string | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, role: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem("access_token"),
  role: localStorage.getItem("role"),
  isAuthenticated: !!localStorage.getItem("access_token"),

  login: (accessToken, refreshToken, role) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("role", role);
    set({ accessToken, role, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("role");
    set({ accessToken: null, role: null, isAuthenticated: false });
  },
}));