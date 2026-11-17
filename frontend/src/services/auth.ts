import type { RegisterPayload, TokenResponse, User } from "@/types";
import { api, tokenStorage } from "./api";

export const authService = {
  async login(email: string, password: string): Promise<User> {
    const { data } = await api.post<TokenResponse>("/auth/login", { email, password });
    tokenStorage.set(data.access_token);
    return data.user;
  },

  async register(payload: RegisterPayload): Promise<User> {
    await api.post<User>("/auth/register", payload);
    return authService.login(payload.email, payload.password);
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>("/users/me");
    return data;
  },

  async logout(): Promise<void> {
    try {
      await api.post("/auth/logout");
    } catch {
      /* token may already be invalid; ignore */
    } finally {
      tokenStorage.clear();
    }
  },
};
