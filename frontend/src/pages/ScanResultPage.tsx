import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { TriageResultCard } from "@/components/triage/TriageResultCard";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getErrorMessage } from "@/lib/errors";
import { triageService } from "@/services/triage";
import type { TriageResult } from "@/types";

export default function ScanResultPage() {
  const { id } = useParams();
  const [result, setResult] = useState<TriageResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    triageService
      .get(Number(id))
      .then(setResult)
      .catch((e) => setError(getErrorMessage(e, "Couldn't load this result")));
  }, [id]);

  return (
    <div className="space-y-6">
      <Button variant="ghost" asChild className="-ml-3">
        <Link to="/scan">
          <ArrowLeft className="size-4" /> Back to skin scan
        </Link>
      </Button>
      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : result ? (
        <TriageResultCard result={result} />
      ) : (
        <Skeleton className="h-96" />
      )}
    </div>
  );
}
