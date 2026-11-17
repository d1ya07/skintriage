import axios from "axios";

export function getErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(err)) {
    if (!err.response) return "Can't reach the server. Is the backend running?";
    const data = err.response.data as { detail?: unknown } | undefined;
    const detail = data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      return String(detail[0].msg).replace(/^Value error, /, "");
    }
  }
  return fallback;
}
