export type Role = "patient" | "doctor" | "admin";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  skin_type: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  skin_type?: string | null;
}

export type AppointmentStatus = "booked" | "confirmed" | "completed" | "cancelled";

export interface Hospital {
  id: number;
  name: string;
  city: string;
  address: string;
}

export interface Doctor {
  id: number;
  name: string;
  specialty: string;
  bio: string | null;
  hospital: Hospital;
}

export interface SlotsResponse {
  doctor_id: number;
  day: string;
  timezone: string;
  slots: string[];
}

export interface Appointment {
  id: number;
  doctor: Doctor;
  scheduled_at: string;
  reason: string;
  status: AppointmentStatus;
  created_at: string;
  cancelled_at: string | null;
  triage_result_id: number | null;
}

export interface AppointmentCreate {
  doctor_id: number;
  scheduled_at: string;
  reason: string;
  triage_result_id?: number | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatAction {
  label: string;
  to: string;
}

export interface ChatReply {
  reply: string;
  refused: boolean;
  source: "guardrail" | "llm" | "faq";
  actions: ChatAction[];
}

export interface AdminStats {
  users_by_role: Record<Role, number>;
  active_users: number;
  hospitals: number;
  doctors: number;
  appointments_by_status: Record<AppointmentStatus, number>;
  triage_results: number;
}
