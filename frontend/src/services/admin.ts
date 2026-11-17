import type { AdminStats, Role, User } from "@/types";
import { api } from "./api";

export const adminService = {
  async stats(): Promise<AdminStats> {
    const { data } = await api.get<AdminStats>("/admin/stats");
    return data;
  },
  async users(): Promise<User[]> {
    const { data } = await api.get<User[]>("/admin/users");
    return data;
  },
  async updateUser(id: number, patch: { role?: Role; is_active?: boolean }): Promise<User> {
    const { data } = await api.patch<User>(`/admin/users/${id}`, patch);
    return data;
  },
};
