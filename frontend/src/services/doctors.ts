import type { Doctor, SlotsResponse } from "@/types";
import { api } from "./api";

export interface DoctorFilters {
  specialty?: string;
  city?: string;
  q?: string;
}

export const doctorService = {
  async list(filters: DoctorFilters = {}): Promise<Doctor[]> {
    const { data } = await api.get<Doctor[]>("/doctors", { params: filters });
    return data;
  },
  async specialties(): Promise<string[]> {
    const { data } = await api.get<string[]>("/doctors/specialties");
    return data;
  },
  async cities(): Promise<string[]> {
    const { data } = await api.get<string[]>("/doctors/cities");
    return data;
  },
  async slots(doctorId: number, day: string): Promise<SlotsResponse> {
    const { data } = await api.get<SlotsResponse>(`/doctors/${doctorId}/slots`, { params: { day } });
    return data;
  },
};
