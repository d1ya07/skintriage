import type { Appointment, AppointmentCreate } from "@/types";
import { api } from "./api";

export type AppointmentScope = "upcoming" | "past" | "all";

export const appointmentService = {
  async book(payload: AppointmentCreate): Promise<Appointment> {
    const { data } = await api.post<Appointment>("/appointments", payload);
    return data;
  },
  async mine(scope: AppointmentScope = "all"): Promise<Appointment[]> {
    const { data } = await api.get<Appointment[]>("/appointments/me", { params: { scope } });
    return data;
  },
  async cancel(id: number): Promise<Appointment> {
    const { data } = await api.post<Appointment>(`/appointments/${id}/cancel`);
    return data;
  },
};
