export const CLINIC_TZ = "Asia/Kolkata";

const dateTimeFmt = new Intl.DateTimeFormat("en-IN", {
  timeZone: CLINIC_TZ,
  weekday: "short",
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const timeFmt = new Intl.DateTimeFormat("en-IN", {
  timeZone: CLINIC_TZ,
  hour: "numeric",
  minute: "2-digit",
});

export const formatDateTime = (iso: string) => dateTimeFmt.format(new Date(iso));
export const formatTime = (iso: string) => timeFmt.format(new Date(iso));

/** Today's date in the clinic's timezone, as YYYY-MM-DD. */
export function clinicToday(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: CLINIC_TZ }).format(new Date());
}

export interface ClinicDay {
  value: string; // YYYY-MM-DD
  weekday: string;
  label: string;
}

/** Next `count` open days (clinic is closed on Sundays). */
export function upcomingClinicDays(count: number): ClinicDay[] {
  const start = new Date(`${clinicToday()}T00:00:00Z`);
  const out: ClinicDay[] = [];
  for (let i = 0; out.length < count && i < count * 2; i++) {
    const d = new Date(start);
    d.setUTCDate(start.getUTCDate() + i);
    if (d.getUTCDay() === 0) continue;
    out.push({
      value: d.toISOString().slice(0, 10),
      weekday: i === 0 ? "Today" : d.toLocaleDateString("en-IN", { weekday: "short", timeZone: "UTC" }),
      label: d.toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "UTC" }),
    });
  }
  return out;
}
