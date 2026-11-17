import { useEffect, useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";
import { StatusBadge } from "@/components/StatusBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getErrorMessage } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import { appointmentService } from "@/services/appointments";
import type { Appointment } from "@/types";

type Tab = "upcoming" | "past";

export default function AppointmentsPage() {
  const [tab, setTab] = useState<Tab>("upcoming");
  const [items, setItems] = useState<Appointment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [toCancel, setToCancel] = useState<Appointment | null>(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    let ignore = false;
    setItems(null);
    setError(null);
    appointmentService
      .mine(tab)
      .then((a) => !ignore && setItems(a))
      .catch((e) => !ignore && setError(getErrorMessage(e, "Couldn't load appointments")));
    return () => {
      ignore = true;
    };
  }, [tab, reloadKey]);

  async function confirmCancel() {
    if (!toCancel) return;
    setCancelling(true);
    try {
      await appointmentService.cancel(toCancel.id);
      toast.success("Appointment cancelled");
      setToCancel(null);
      setReloadKey((k) => k + 1);
    } catch (e) {
      toast.error(getErrorMessage(e, "Couldn't cancel"));
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">My appointments</h1>
          <p className="text-muted-foreground">All times are in IST.</p>
        </div>
        <Button asChild>
          <Link to="/doctors">Book new</Link>
        </Button>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="past">Past & cancelled</TabsTrigger>
        </TabsList>
      </Tabs>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="p-0">
          {items === null && !error ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : items && items.length === 0 ? (
            <div className="space-y-3 p-12 text-center text-muted-foreground">
              <p>{tab === "upcoming" ? "No upcoming appointments." : "Nothing here yet."}</p>
              {tab === "upcoming" && (
                <Button variant="outline" asChild>
                  <Link to="/doctors">Find a doctor</Link>
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date & time</TableHead>
                    <TableHead>Specialist</TableHead>
                    <TableHead>Hospital</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items?.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="whitespace-nowrap font-medium">
                        {formatDateTime(a.scheduled_at)}
                      </TableCell>
                      <TableCell>
                        <div>{a.doctor.name}</div>
                        <div className="text-xs text-muted-foreground">{a.doctor.specialty}</div>
                      </TableCell>
                      <TableCell>
                        <div>{a.doctor.hospital.name}</div>
                        <div className="text-xs text-muted-foreground">{a.doctor.hospital.city}</div>
                      </TableCell>
                      <TableCell className="max-w-56 truncate" title={a.reason}>
                        {a.reason}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={a.status} />
                        {a.cancelled_at && (
                          <div className="mt-1 text-xs text-muted-foreground">
                            on {formatDateTime(a.cancelled_at)}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {tab === "upcoming" && (a.status === "booked" || a.status === "confirmed") && (
                          <Button variant="outline" size="sm" onClick={() => setToCancel(a)}>
                            Cancel
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!toCancel} onOpenChange={(open) => !open && setToCancel(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel this appointment?</DialogTitle>
            <DialogDescription>
              {toCancel &&
                `${toCancel.doctor.name}, ${formatDateTime(toCancel.scheduled_at)}. The slot will be released for others.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setToCancel(null)}>
              Keep it
            </Button>
            <Button variant="destructive" onClick={confirmCancel} disabled={cancelling}>
              {cancelling ? "Cancelling..." : "Yes, cancel"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
