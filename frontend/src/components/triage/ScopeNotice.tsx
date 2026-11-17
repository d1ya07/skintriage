import { Info } from "lucide-react";

export function ScopeNotice() {
  return (
    <div className="flex gap-2 rounded-lg border border-sky-200 bg-sky-50 p-3 text-sm text-sky-950 dark:border-sky-900 dark:bg-sky-950 dark:text-sky-100">
      <Info className="mt-0.5 size-4 shrink-0" />
      <div>
        <p className="font-medium">What this scan can assess</p>
        <p>
          Moles and pigmented skin spots only. It <strong>cannot</strong> assess acne or pimples, rashes, insect bites,
          burns, cuts, warts or infections, and results for those will be unreliable.
        </p>
      </div>
    </div>
  );
}
