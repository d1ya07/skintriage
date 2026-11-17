import { Download } from "lucide-react";
import { useEffect, useState } from "react";
import { UrgencyBadge } from "@/components/triage/UrgencyBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getErrorMessage } from "@/lib/errors";
import { adminService } from "@/services/admin";
import type { Analytics } from "@/types";

type Range = "7" | "30" | "90";
const SERIES = { scans: "var(--chart-1)", bookings: "var(--chart-2)" };
const pct = (x: number) => `${Math.round(x * 100)}%`;

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl tabular-nums">{value}</CardTitle>
      </CardHeader>
      {sub && <CardContent className="text-xs text-muted-foreground">{sub}</CardContent>}
    </Card>
  );
}

function HBar({ share, color = SERIES.scans }: { share: number; color?: string }) {
  return (
    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
      <div
        className="h-full rounded-full"
        style={{ width: `${share > 0 ? Math.max(share * 100, 2) : 0}%`, background: color }}
      />
    </div>
  );
}

function DailyChart({ data }: { data: Analytics["daily"] }) {
  const max = Math.max(1, ...data.map((d) => Math.max(d.scans, d.bookings)));
  const label = (iso: string) =>
    new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "UTC" });
  return (
    <div className="space-y-2">
      <div className="flex gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-sm" style={{ background: SERIES.scans }} /> Skin scans
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-sm" style={{ background: SERIES.bookings }} /> Bookings
        </span>
        <span className="ml-auto">max {max} per day</span>
      </div>
      <div className="flex h-40 items-end gap-[2px] border-b border-border">
        {data.map((d) => (
          <div
            key={d.day}
            title={`${label(d.day)}: ${d.scans} scan(s), ${d.bookings} booking(s)`}
            className="flex h-full flex-1 items-end gap-[2px] rounded-sm hover:bg-muted/60"
          >
            <div className="flex-1 rounded-t-[4px]" style={{ height: `${(d.scans / max) * 100}%`, background: SERIES.scans }} />
            <div
              className="flex-1 rounded-t-[4px]"
              style={{ height: `${(d.bookings / max) * 100}%`, background: SERIES.bookings }}
            />
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{label(data[0].day)}</span>
        <span>{label(data[Math.floor(data.length / 2)].day)}</span>
        <span>{label(data[data.length - 1].day)}</span>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [range, setRange] = useState<Range>("30");
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    setData(null);
    setError(null);
    adminService
      .analytics(Number(range))
      .then((d) => !ignore && setData(d))
      .catch((e) => !ignore && setError(getErrorMessage(e, "Couldn't load analytics")));
    return () => {
      ignore = true;
    };
  }, [range]);

  function downloadCsv() {
    if (!data) return;
    const rows = ["day,scans,bookings", ...data.daily.map((d) => `${d.day},${d.scans},${d.bookings}`)];
    const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `skintriage-daily-${range}d.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">How patients move from a skin scan to care.</p>
        </div>
        <div className="flex items-center gap-2">
          <Tabs value={range} onValueChange={(v) => setRange(v as Range)}>
            <TabsList>
              <TabsTrigger value="7">7 days</TabsTrigger>
              <TabsTrigger value="30">30 days</TabsTrigger>
              <TabsTrigger value="90">90 days</TabsTrigger>
            </TabsList>
          </Tabs>
          <Button variant="outline" size="sm" onClick={downloadCsv} disabled={!data}>
            <Download className="size-4" /> CSV
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!data ? (
        !error && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-28" />
            ))}
          </div>
        )
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Kpi label="Skin scans" value={String(data.total_scans)} sub={`last ${data.days} days`} />
            <Kpi
              label="Scan → booking"
              value={pct(data.triage_to_booking_rate)}
              sub={`${data.scans_booked} of ${data.total_scans} scans led to a booking`}
            />
            <Kpi
              label="Urgent referrals booked"
              value={data.urgent_scans ? pct(data.urgent_booking_rate) : "None"}
              sub={`${data.urgent_booked} of ${data.urgent_scans} high-urgency scans`}
            />
            <Kpi
              label="Median time to book"
              value={data.median_hours_to_booking === null ? "None" : `${data.median_hours_to_booking} h`}
              sub="from scan to booking"
            />
            <Kpi label="Uncertain results" value={pct(data.uncertain_rate)} sub="possibly outside the model's scope" />
            <Kpi
              label="Appointments"
              value={String(data.appointments_total)}
              sub={`${data.appointments_from_scan} booked from a scan`}
            />
            <Kpi label="Cancellation rate" value={pct(data.cancellation_rate)} />
            <Kpi label="Completion rate" value={pct(data.completion_rate)} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Urgency mix and booking rate</CardTitle>
                <CardDescription>Share of scans at each urgency, and how many of those were booked</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {data.by_urgency.map((u) => (
                  <div key={u.urgency} className="space-y-1.5" title={`${u.scans} scans, ${u.booked} booked`}>
                    <div className="flex items-center justify-between gap-2 text-sm">
                      <UrgencyBadge level={u.urgency} />
                      <span className="tabular-nums text-muted-foreground">
                        {u.scans} scans ({pct(data.total_scans ? u.scans / data.total_scans : 0)}) ·{" "}
                        <span className="text-foreground">{pct(u.booking_rate)} booked</span>
                      </span>
                    </div>
                    <HBar share={data.total_scans ? u.scans / data.total_scans : 0} />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Predicted conditions</CardTitle>
                <CardDescription>Model's top suggestion per scan (not a diagnosis)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.by_condition.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No scans in this period.</p>
                ) : (
                  data.by_condition.map((c) => (
                    <div key={c.code} className="flex items-center gap-3 text-sm" title={`${c.count} scan(s)`}>
                      <span className="w-48 shrink-0 truncate">{c.label}</span>
                      <HBar share={c.count / data.total_scans} />
                      <span className="w-8 text-right tabular-nums">{c.count}</span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Scans and bookings per day</CardTitle>
              <CardDescription>Hover a day for exact numbers. Use CSV for a table view.</CardDescription>
            </CardHeader>
            <CardContent>
              <DailyChart data={data.daily} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
