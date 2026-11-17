import {
  Brain,
  CalendarCheck,
  Camera,
  Gauge,
  MessageCircle,
  ShieldAlert,
  Stethoscope,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { dashboardPath } from "@/lib/roles";

const STEPS: { icon: LucideIcon; title: string; desc: string }[] = [
  { icon: Camera, title: "1. Upload a photo", desc: "Take a clear, close-up photo of the skin concern." },
  {
    icon: Brain,
    title: "2. AI triage",
    desc: "A model trained on dermatoscopic images suggests a likely condition with a confidence score.",
  },
  {
    icon: Gauge,
    title: "3. Urgency & referral",
    desc: "A rule engine assigns low, moderate or high urgency and the right type of specialist.",
  },
  {
    icon: CalendarCheck,
    title: "4. Book a specialist",
    desc: "Pick a matched doctor and a time slot in a few clicks.",
  },
];

const FEATURES: { icon: LucideIcon; title: string; desc: string }[] = [
  {
    icon: ShieldAlert,
    title: "Urgent cases flagged",
    desc: "High-urgency results show an urgent referral banner so nothing serious waits in a queue.",
  },
  {
    icon: Stethoscope,
    title: "Specialist directory",
    desc: "Dermatologists, dermato-oncologists, surgeons and GPs across partner hospitals.",
  },
  {
    icon: MessageCircle,
    title: "Help assistant",
    desc: "An in-app assistant answers platform questions and never gives medical advice.",
  },
];

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-20 py-16">
      <section className="flex flex-col items-center gap-6 text-center">
        <span className="rounded-full border px-3 py-1 text-xs text-muted-foreground">
          AI-assisted skin triage & referral
        </span>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-6xl">
          Know how urgent your skin concern is.
        </h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          Upload a photo, get an AI-assisted urgency level, and book the right specialist, all in one place.
        </p>
        <div className="flex gap-3">
          {user ? (
            <Button size="lg" asChild>
              <Link to={dashboardPath(user.role)}>Go to dashboard</Link>
            </Button>
          ) : (
            <>
              <Button size="lg" asChild>
                <Link to="/register">Get started</Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link to="/login">Log in</Link>
              </Button>
            </>
          )}
        </div>
      </section>

      <section className="space-y-8">
        <h2 className="text-center text-2xl font-semibold">How it works</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(({ icon: Icon, title, desc }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="size-8" />
                <CardTitle className="pt-2 text-base">{title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">{desc}</CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="space-y-2">
            <Icon className="size-6" />
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{desc}</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-amber-300 bg-amber-50 p-6 text-amber-950 dark:bg-amber-950 dark:text-amber-100">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <ShieldAlert className="size-5" /> Decision support, not diagnosis
        </h2>
        <p className="mt-2 text-sm">
          SkinTriage helps you decide how quickly to seek care and who to see. It does not diagnose any
          condition and is not a substitute for a medical professional. If you think you have a medical
          emergency, call 112.
        </p>
      </section>
    </div>
  );
}
