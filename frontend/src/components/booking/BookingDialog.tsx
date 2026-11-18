import axios from "axios";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/errors";
import { formatDateTime, formatTime, upcomingClinicDays } from "@/lib/format";
import { cn } from "@/lib/utils";
import { appointmentService } from "@/services/appointments";
import { doctorService } from "@/services/doctors";
import type { Doctor } from "@/types";

interface Props {
  doctor: Doctor | null;
  triageResultId?: number | null;
  onClose: () => void;
}

export function BookingDialog({ doctor, triageResultId, onClose }: Props) {
  const navigate = useNavigate();
  const days = useMemo(() => upcomingClinicDays(14), []);
  const [day, setDay] = useState(days[0]?.value ?? "");
  const [slots, setSlots] = useState<string[] | null>(null);
  const [slot, setSlot] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!doctor || !day) return;
    let ignore = false;
    setSlots(null);
    setSlot(null);
    doctorService
      .slots(doctor.id, day)
      .then((r) => !ignore && setSlots(r.slots))
      .catch((e) => {
        if (!ignore) {
          setSlots([]);
          setError(getErrorMessage(e, "Couldn't load slots"));
        }
      });
    return () => {
      ignore = true;
    };
  }, [doctor, day, reloadKey]);

  async function confirm() {
    if (!doctor || !slot) return;
    if (reason.trim().length < 3) {
      setError("Please describe the reason for your visit (at least 3 characters)");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await appointmentService.book({
        doctor_id: doctor.id,
        scheduled_at: slot,
        reason: reason.trim(),
        triage_result_id: triageResultId ?? null,
      });
      toast.success(`Booked with ${doctor.name}`, { description: formatDateTime(slot) });
      onClose();
      navigate("/appointments");
    } catch (e) {
      setError(getErrorMessage(e, "Booking failed"));
      if (axios.isAxiosError(e) && e.response?.status === 409) setReloadKey((k) => k + 1);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={!!doctor} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto overflow-x-hidden sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Book with {doctor?.name}</DialogTitle>
          <DialogDescription>
            {doctor?.specialty} · {doctor?.hospital.name}, {doctor?.hospital.city}
          </DialogDescription>
        </DialogHeader>

        <div className="min-w-0 space-y-5">
          <div className="space-y-2">
            <Label>Date</Label>
            <div className="-mx-1 flex w-full min-w-0 gap-2 overflow-x-auto px-1 pb-2">
              {days.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => setDay(d.value)}
                  className={cn(
                    "flex shrink-0 flex-col items-center rounded-md border px-3 py-2 text-sm transition-colors",
                    d.value === day ? "border-primary bg-primary text-primary-foreground" : "hover:bg-muted",
                  )}
                >
                  <span className="text-xs opacity-80">{d.weekday}</span>
                  <span className="font-medium">{d.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Time (IST)</Label>
            {slots === null ? (
              <div className="grid grid-cols-4 gap-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-9" />
                ))}
              </div>
            ) : slots.length === 0 ? (
              <p className="text-sm text-muted-foreground">No free slots this day. Try another date.</p>
            ) : (
              <div className="grid max-h-48 grid-cols-3 gap-2 overflow-y-auto sm:grid-cols-4">
                {slots.map((s) => (
                  <Button
                    key={s}
                    type="button"
                    size="sm"
                    className="min-w-0 px-1 text-xs sm:text-sm"
                    variant={s === slot ? "default" : "outline"}
                    onClick={() => setSlot(s)}
                  >
                    {formatTime(s)}
                  </Button>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">Reason for visit</Label>
            <Textarea
              id="reason"
              rows={3}
              maxLength={500}
              placeholder="e.g. A mole on my back has changed shape"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={confirm} disabled={!slot || submitting}>
            {submitting ? "Booking..." : slot ? `Confirm ${formatTime(slot)}` : "Pick a time"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
