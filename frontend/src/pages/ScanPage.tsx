import { ImageUp, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState, type DragEvent } from "react";
import { Link } from "react-router";
import { toast } from "sonner";
import { ScopeNotice } from "@/components/triage/ScopeNotice";
import { TriageResultCard } from "@/components/triage/TriageResultCard";
import { UrgencyBadge } from "@/components/triage/UrgencyBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getErrorMessage } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { triageService } from "@/services/triage";
import type { TriageResult } from "@/types";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024;

const TIPS = [
  "Use good natural light and avoid flash glare",
  "Hold the camera steady so the spot is in sharp focus",
  "Fill most of the frame with the area of concern",
  "One spot per photo, no filters",
];

export default function ScanPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [history, setHistory] = useState<TriageResult[] | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    triageService
      .mine()
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [result]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function pick(f: File | undefined) {
    setError(null);
    setResult(null);
    if (!f) return;
    if (!ACCEPTED.includes(f.type)) {
      setError("Please choose a JPG, PNG or WEBP image. iPhone HEIC photos need to be exported as JPG first.");
      return;
    }
    if (f.size > MAX_BYTES) {
      setError("That image is too large (max 10 MB).");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    pick(e.dataTransfer.files?.[0]);
  }

  async function analyse() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setProgress(0);
    try {
      const r = await triageService.create(file, setProgress);
      setResult(r);
      if (r.urgent_referral) toast.warning("Urgent referral recommended");
      else toast.success("Analysis complete");
    } catch (e) {
      setError(getErrorMessage(e, "Analysis failed. Please try again."));
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setFile(null);
    setPreview(null);
    setResult(null);
    setAcknowledged(false);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Skin scan</h1>
          <p className="text-muted-foreground">Upload a photo for an AI-assisted urgency check.</p>
        </div>
        {result && (
          <Button variant="outline" onClick={reset}>
            <RotateCcw className="size-4" /> Scan another photo
          </Button>
        )}
      </div>

      {result ? (
        <TriageResultCard result={result} />
      ) : (
        <Card>
          <CardContent className="grid gap-6 pt-6 md:grid-cols-2">
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={cn(
                "flex aspect-square cursor-pointer flex-col items-center justify-center gap-3 overflow-hidden rounded-xl border-2 border-dashed text-center transition-colors",
                dragOver ? "border-primary bg-muted" : "hover:bg-muted/50",
              )}
            >
              {preview ? (
                <img src={preview} alt="Selected photo preview" className="h-full w-full object-cover" />
              ) : (
                <>
                  <ImageUp className="size-10 text-muted-foreground" />
                  <p className="font-medium">Drop a photo here or click to choose</p>
                  <p className="text-xs text-muted-foreground">JPG, PNG or WEBP, up to 10 MB</p>
                </>
              )}
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED.join(",")}
                className="hidden"
                onChange={(e) => pick(e.target.files?.[0])}
              />
            </div>

            <div className="flex flex-col gap-5">
              <ScopeNotice />
              <div>
                <h2 className="font-semibold">Tips for a useful photo</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {TIPS.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
                <p className="mt-3 text-xs text-muted-foreground">
                  The model was trained on close-up dermatoscopic images, so ordinary phone photos may give less
                  reliable results.
                </p>
              </div>

              <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-0.5 size-4"
                  checked={acknowledged}
                  onChange={(e) => setAcknowledged(e.target.checked)}
                />
                <span>
                  I understand this is an AI-assisted triage suggestion, <strong>not a diagnosis</strong>, and I
                  should consult a medical professional.
                </span>
              </label>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="mt-auto space-y-2">
                {busy && (
                  <div className="space-y-1">
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {progress < 100 ? `Uploading... ${progress}%` : "Analysing image..."}
                    </p>
                  </div>
                )}
                <div className="flex gap-2">
                  <Button className="flex-1" disabled={!file || !acknowledged || busy} onClick={analyse}>
                    {busy ? "Analysing..." : "Analyse photo"}
                  </Button>
                  {file && !busy && (
                    <Button variant="outline" onClick={reset}>
                      Clear
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Your scan history</CardTitle>
          <CardDescription>Previous results are saved to your account.</CardDescription>
        </CardHeader>
        <CardContent>
          {history === null ? (
            <Skeleton className="h-16" />
          ) : history.length === 0 ? (
            <p className="text-sm text-muted-foreground">No scans yet.</p>
          ) : (
            <ul className="divide-y">
              {history.map((h) => (
                <li key={h.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-medium">{h.predicted_label}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(h.created_at)} · {Math.round(h.confidence * 100)}% confidence
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <UrgencyBadge level={h.urgency_level} />
                    <Button size="sm" variant="outline" asChild>
                      <Link to={`/scan/${h.id}`}>View</Link>
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
