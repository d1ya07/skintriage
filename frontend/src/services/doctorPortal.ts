import type { DoctorAppointment, DoctorMe } from "@/types";
import { api } from "./api";

export type DoctorScope = "upcoming" | "pending" | "history";

export const doctorPortal = {
  async me(): Promise<DoctorMe> {
    const { data } = await api.get<DoctorMe>("/doctor/me");
    return data;
  },
  async appointments(scope: DoctorScope): Promise<DoctorAppointment[]> {
    const { data } = await api.get<DoctorAppointment[]>("/doctor/appointments", { params: { scope } });
    return data;
  },
  async confirm(id: number): Promise<DoctorAppointment> {
    const { data } = await api.post<DoctorAppointment>(`/doctor/appointments/${id}/confirm`);
    return data;
  },
  async complete(id: number): Promise<DoctorAppointment> {
    const { data } = await api.post<DoctorAppointment>(`/doctor/appointments/${id}/complete`);
    return data;
  },
};
