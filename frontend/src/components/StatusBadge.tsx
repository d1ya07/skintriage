import { Badge } from "@/components/ui/badge";
import type { AppointmentStatus } from "@/types";

const STYLES: Record<AppointmentStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  booked: { label: "Booked", variant: "default" },
  confirmed: { label: "Confirmed", variant: "secondary" },
  completed: { label: "Completed", variant: "outline" },
  cancelled: { label: "Cancelled", variant: "destructive" },
};

export function StatusBadge({ status }: { status: AppointmentStatus }) {
  const s = STYLES[status];
  return <Badge variant={s.variant}>{s.label}</Badge>;
}
