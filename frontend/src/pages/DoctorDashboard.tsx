import { CalendarCheck, CheckCircle2, MapPin } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { StatusBadge } from "@/components/StatusBadge";
import { TriageResultCard } from "@/components/triage/TriageResultCard";
import { UrgencyBadge } from "@/components/triage/UrgencyBadge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getErrorMessage } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { doctorPortal, type DoctorScope } from "@/services/doctorPortal";
import { triageService } from "@/services/triage";
import type { DoctorAppointment, DoctorMe, TriageResult } from "@/types";

function Stat({ label, value, alert }: { label: string; value?: number; alert?: boolean }) {
  return (
    <Card className={cn(alert && value ? "border-red-300 bg-red-50 dark:bg-red-950" : "")}>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl">{value ?? <Skeleton className="h-8 w-10" />}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function TriageDialog({ id, onClose }: { id: number | null; onClose: () => void }) {
  const [result, setResult] = useState<TriageResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id === null) return;
    let ignore = false;
    setResult(null);
    setError(null);
    triageService
      .get(id)
      .then((r) => !ignore && setResult(r))
      .catch((e) => !ignore && setError(getErrorMessage(e, "Couldn't load the scan")));
    return () => {
      ignore = true;
    };
  }, [id]);

  return (
    <Dialog open={id !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Patient skin scan</DialogTitle>
        </DialogHeader>
        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : result ? (
          <TriageResultCard result={result} showBookButton={false} />
        ) : (
          <Skeleton className="h-80" />
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function DoctorDashboard() {
  const [me, setMe] = useState<DoctorMe | null>(null);
  const [blocked, setBlocked] = useState<string | null>(null);
  const [scope, setScope] = useState<DoctorScope>("upcoming");
  const [items, setItems] = useState<DoctorAppointment[] | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [triageId, setTriageId] = useState<number | null>(null);

  useEffect(() => {
    doctorPortal
      .me()
      .then(setMe)
      .catch((e) => setBlocked(getErrorMessage(e, "Couldn't load your doctor profile")));
  }, [reloadKey]);

  useEffect(() => {
    if (blocked) return;
    let ignore = false;
    setItems(null);
    doctorPortal
      .appointments(scope)
      .then((a) => !ignore && setItems(a))
      .catch(() => !ignore && setItems([]));
    return () => {
      ignore = true;
    };
  }, [scope, reloadKey, blocked]);

  async function act(a: DoctorAppointment, action: "confirm" | "complete") {
    setBusyId(a.id);
    try {
      await doctorPortal[action](a.id);
      toast.success(action === "confirm" ? "Appointment confirmed" : "Marked as completed");
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(getErrorMessage(e, "Action failed"));
    } finally {
      setBusyId(null);
    }
  }

  if (blocked) {
    return (
      <Alert>
        <AlertTitle>Doctor profile not linked</AlertTitle>
        <AlertDescription>{blocked}</AlertDescription>
      </Alert>
    );
  }

  const now = Date.now();
  const s = me?.stats;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">{me ? me.doctor.name : <Skeleton className="h-9 w-56" />}</h1>
          {me && (
            <p className="flex flex-wrap items-center gap-2 text-muted-foreground">
              <Badge variant="secondary">{me.doctor.specialty}</Badge>
              <MapPin className="size-4" /> {me.doctor.hospital.name}, {me.doctor.hospital.city}
            </p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Stat label="Today" value={s?.today} />
        <Stat label="Awaiting confirmation" value={s?.awaiting_confirmation} />
        <Stat label="Needs completion" value={s?.to_complete} />
        <Stat label="Urgent referrals upcoming" value={s?.urgent_upcoming} alert />
        <Stat label="Completed" value={s?.completed} />
      </div>

      <Tabs value={scope} onValueChange={(v) => setScope(v as DoctorScope)}>
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="pending">Needs completion</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>
      </Tabs>

      <Card>
        <CardContent className="p-0">
          {items === null ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <p className="p-12 text-center text-muted-foreground">Nothing here.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>When (IST)</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Skin scan</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((a) => {
                    const t = new Date(a.scheduled_at).getTime();
                    const canConfirm = a.status === "booked" && t > now;
                    const canComplete = (a.status === "booked" || a.status === "confirmed") && t <= now;
                    const busy = busyId === a.id;
                    return (
                      <TableRow
                        key={a.id}
                        className={cn(a.triage?.urgent_referral && a.status !== "cancelled" && "bg-red-50/70 dark:bg-red-950/40")}
                      >
                        <TableCell className="whitespace-nowrap font-medium">{formatDateTime(a.scheduled_at)}</TableCell>
                        <TableCell>
                          <div>{a.patient.name}</div>
                          <div className="text-xs text-muted-foreground">{a.patient.email}</div>
                          {a.patient.skin_type && (
                            <div className="text-xs text-muted-foreground">Skin type {a.patient.skin_type}</div>
                          )}
                        </TableCell>
                        <TableCell className="max-w-56 truncate" title={a.reason}>
                          {a.reason}
                        </TableCell>
                        <TableCell>
                          {a.triage ? (
                            <button
                              type="button"
                              onClick={() => setTriageId(a.triage!.id)}
                              className="space-y-1 text-left hover:underline"
                            >
                              <UrgencyBadge level={a.triage.urgency_level} />
                              <div className="text-xs text-muted-foreground">
                                {a.triage.predicted_label} ({Math.round(a.triage.confidence * 100)}%){a.triage.uncertain ? " · uncertain" : ""}
                              </div>
                            </button>
                          ) : (
                            <span className="text-xs text-muted-foreground">None</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={a.status} />
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            {canConfirm && (
                              <Button size="sm" disabled={busy} onClick={() => void act(a, "confirm")}>
                                <CalendarCheck className="size-4" /> Confirm
                              </Button>
                            )}
                            {canComplete && (
                              <Button size="sm" variant="outline" disabled={busy} onClick={() => void act(a, "complete")}>
                                <CheckCircle2 className="size-4" /> Mark completed
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <TriageDialog id={triageId} onClose={() => setTriageId(null)} />
    </div>
  );
}
