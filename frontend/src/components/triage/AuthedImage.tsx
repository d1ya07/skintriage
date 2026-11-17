import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { triageService } from "@/services/triage";

export function AuthedImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;
    triageService
      .imageBlobUrl(src)
      .then((u) => {
        if (cancelled) URL.revokeObjectURL(u);
        else {
          objectUrl = u;
          setUrl(u);
        }
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src]);

  if (failed) {
    return (
      <div className={cn("flex aspect-square w-full items-center justify-center rounded-lg bg-muted text-sm text-muted-foreground", className)}>
        Image unavailable
      </div>
    );
  }
  if (!url) return <Skeleton className={cn("aspect-square w-full rounded-lg", className)} />;
  return <img src={url} alt={alt} className={cn("w-full rounded-lg object-cover", className)} />;
}
