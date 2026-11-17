import type { TriageResult } from "@/types";
import { api } from "./api";

export const triageService = {
  async create(file: File, onProgress?: (pct: number) => void): Promise<TriageResult> {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post<TriageResult>("/triage", form, {
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
    return data;
  },
  async mine(): Promise<TriageResult[]> {
    const { data } = await api.get<TriageResult[]>("/triage/me");
    return data;
  },
  async get(id: number): Promise<TriageResult> {
    const { data } = await api.get<TriageResult>(`/triage/${id}`);
    return data;
  },
  /** Images need the auth header, so fetch as a blob and return a local object URL. */
  async imageBlobUrl(imageUrl: string): Promise<string> {
    const path = imageUrl.replace(/^\/api/, "");
    const { data } = await api.get<Blob>(path, { responseType: "blob" });
    return URL.createObjectURL(data);
  },
};
