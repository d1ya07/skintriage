import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { UrgencyLevel } from "@/types";

const STYLES: Record<UrgencyLevel, { label: string; className: string }> = {
  low: {
    label: "Low urgency",
    className: "border-emerald-300 bg-emerald-50 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100",
  },
  moderate: {
    label: "Moderate urgency",
    className: "border-amber-300 bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-100",
  },
  high: {
    label: "High urgency",
    className: "border-red-300 bg-red-50 text-red-900 dark:bg-red-950 dark:text-red-100",
  },
};

export function UrgencyBadge({ level, className }: { level: UrgencyLevel; className?: string }) {
  const s = STYLES[level];
  return (
    <Badge variant="outline" className={cn(s.className, className)}>
      {s.label}
    </Badge>
  );
}
