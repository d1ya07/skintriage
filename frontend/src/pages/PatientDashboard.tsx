import { CalendarDays, ScanLine, Stethoscope, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";
import { StatusBadge } from "@/components/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { appointmentService } from "@/services/appointments";
import type { Appointment } from "@/types";

interface ActionProps {
  icon: LucideIcon;
  title: string;
  desc: string;
  to?: string;
  badge?: string;
}

function ActionCard({ icon: Icon, title, desc, to, badge }: ActionProps) {
  const card = (
    <Card className={cn("h-full transition-colors", to ? "hover:border-primary" : "opacity-60")}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <Icon className="size-6" />
          {badge && <Badge variant="outline">{badge}</Badge>}
        </div>
        <CardTitle className="pt-2">{title}</CardTitle>
        <CardDescription>{desc}</CardDescription>
      </CardHeader>
    </Card>
  );
  return to ? <Link to={to}>{card}</Link> : card;
}

export default function PatientDashboard() {
  const { user } = useAuth();
  const [next, setNext] = useState<Appointment | null | undefined>(undefined);

  useEffect(() => {
    appointmentService
      .mine("upcoming")
      .then((a) => setNext(a[0] ?? null))
      .catch(() => setNext(null));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Hi, {user?.name.split(" ")[0]} 👋</h1>
        <p className="text-muted-foreground">What would you like to do today?</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <ActionCard
          icon={ScanLine}
          title="Skin scan"
          desc="Upload a photo for an AI-assisted urgency check."
          to="/scan"
        />
        <ActionCard
          icon={Stethoscope}
          title="Find a doctor"
          desc="Browse specialists and book a slot."
          to="/doctors"
        />
        <ActionCard
          icon={CalendarDays}
          title="My appointments"
          desc="See upcoming and past visits."
          to="/appointments"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Next appointment</CardTitle>
        </CardHeader>
        <CardContent>
          {next === undefined ? (
            <Skeleton className="h-12" />
          ) : next === null ? (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-muted-foreground">You have no upcoming appointments.</p>
              <Button variant="outline" asChild>
                <Link to="/doctors">Book one</Link>
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-medium">{formatDateTime(next.scheduled_at)}</p>
                <p className="text-sm text-muted-foreground">
                  {next.doctor.name} · {next.doctor.specialty} · {next.doctor.hospital.name}
                </p>
              </div>
              <StatusBadge status={next.status} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
