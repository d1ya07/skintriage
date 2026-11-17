import { describe, expect, it } from "vitest";
import { formatTime, upcomingClinicDays } from "./format";

describe("format helpers", () => {
  it("shows times in IST", () => {
    // 04:30 UTC is 10:00 in India
    expect(formatTime("2026-11-18T04:30:00Z")).toMatch(/10:00/);
  });

  it("lists the requested number of open days and skips Sundays", () => {
    const days = upcomingClinicDays(14);
    expect(days).toHaveLength(14);
    for (const d of days) {
      expect(new Date(`${d.value}T00:00:00Z`).getUTCDay()).not.toBe(0);
    }
  });
});
