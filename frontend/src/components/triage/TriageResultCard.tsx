import { AlertTriangle, Info, Stethoscope } from "lucide-react";
import { Link } from "react-router";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { TriageResult } from "@/types";
import { AuthedImage } from "./AuthedImage";
import { UrgencyBadge } from "./UrgencyBadge";

const pct = (p: number) => `${Math.round(p * 100)}%`;

export function TriageResultCard({
  result,
  showImage = true,
  showBookButton = true,
}: {
  result: TriageResult;
  showImage?: boolean;
  showBookButton?: boolean;
}) {
  const high = result.urgency_level === "high";
  const bookHref = result.specialist_type
    ? `/doctors?specialty=${encodeURIComponent(result.specialist_type)}&triage=${result.id}`
    : `/doctors?triage=${result.id}`;

  return (
    <div className="space-y-4">
      {high && (
        <Alert variant="destructive" className="border-red-400">
          <AlertTriangle className="size-5" />
          <AlertTitle>Urgent referral recommended</AlertTitle>
          <AlertDescription>
            This result has been flagged for urgent review. Please book a {result.specialist_type ?? "specialist"} as
            soon as possible. If you think this is a medical emergency, call 112.
          </AlertDescription>
        </Alert>
      )}

      {result.uncertain && (
        <Alert className="border-amber-300 bg-amber-50 text-amber-950 dark:bg-amber-950 dark:text-amber-100">
          <Info className="size-5" />
          <AlertTitle>This image may be outside what the model can assess</AlertTitle>
          <AlertDescription>
            The model only knows 7 types of pigmented skin lesion and was trained on close-up dermatoscopic images.
            Acne, rashes, bites and similar conditions give unreliable results. If you are worried, book a doctor anyway.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className={cn("grid gap-6 pt-6", showImage && "md:grid-cols-[260px_1fr]")}>
          {showImage && <AuthedImage src={result.image_url} alt="Uploaded skin photo" />}

          <div className="space-y-5">
            <div className="space-y-2">
              {result.uncertain ? (
                <>
                  <p className="text-sm text-muted-foreground">AI suggestion</p>
                  <h2 className="text-2xl font-bold">Uncertain result</h2>
                  <p className="text-sm text-muted-foreground">
                    Closest match among the lesion types the model knows:{" "}
                    <strong className="text-foreground">{result.predicted_label}</strong> ({pct(result.confidence)})
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">Most likely (AI suggestion)</p>
                  <h2 className="text-2xl font-bold">{result.predicted_label}</h2>
                </>
              )}
              <div className="flex flex-wrap items-center gap-2">
                <UrgencyBadge level={result.urgency_level} />
                {result.specialist_type && (
                  <span className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Stethoscope className="size-4" /> {result.specialist_type}
                  </span>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Model confidence</span>
                <span className="font-medium">{pct(result.confidence)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-primary" style={{ width: pct(result.confidence) }} />
              </div>
            </div>

            <p className="text-sm">{result.advice}</p>

            {showBookButton && (
            <Button asChild variant={high ? "destructive" : "default"} className="w-full sm:w-auto">
              <Link to={bookHref}>
                {high ? "Book urgent appointment" : "Book matched specialist"}
                {result.specialist_type ? ` (${result.specialist_type})` : ""}
              </Link>
            </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Why this result</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
              {result.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">All class probabilities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {result.probabilities.map((p) => (
              <div key={p.code} className="space-y-1">
                <div className="flex justify-between gap-2 text-xs">
                  <span className="truncate">{p.label}</span>
                  <span className="tabular-nums">{pct(p.probability)}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn("h-full rounded-full", p.code === result.predicted_condition ? "bg-primary" : "bg-muted-foreground/40")}
                    style={{ width: pct(p.probability) }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <p className="flex items-start gap-2 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <span>
          {result.disclaimer} Scanned {formatDateTime(result.created_at)}
          {result.model_version ? ` · model ${result.model_version}` : ""}.
        </span>
      </p>
    </div>
  );
}
