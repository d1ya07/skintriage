import { cn } from "@/lib/utils";

export function Disclaimer({ className }: { className?: string }) {
  return (
    <p className={cn("text-center text-xs text-muted-foreground", className)}>
      ⚕️ SkinTriage is a clinical decision-support tool, <strong>not a diagnostic device</strong>.
      Results are not a diagnosis. Always consult a qualified medical professional.
    </p>
  );
}
