import type { Role } from "@/types";

export function dashboardPath(role: Role): string {
  if (role === "admin") return "/admin";
  if (role === "doctor") return "/doctor";
  return "/patient";
}
