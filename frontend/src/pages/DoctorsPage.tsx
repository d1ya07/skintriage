import { MapPin, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { BookingDialog } from "@/components/booking/BookingDialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { getErrorMessage } from "@/lib/errors";
import { doctorService } from "@/services/doctors";
import type { Doctor } from "@/types";

export default function DoctorsPage() {
  const [params] = useSearchParams();
  const triageParam = params.get("triage");
  const triageResultId = triageParam ? Number(triageParam) : null;

  const [specialty, setSpecialty] = useState(params.get("specialty") ?? "all");
  const [city, setCity] = useState("all");
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [specialties, setSpecialties] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [doctors, setDoctors] = useState<Doctor[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Doctor | null>(null);

  useEffect(() => {
    Promise.all([doctorService.specialties(), doctorService.cities()])
      .then(([s, c]) => {
        setSpecialties(s);
        setCities(c);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    let ignore = false;
    setDoctors(null);
    setError(null);
    doctorService
      .list({
        specialty: specialty === "all" ? undefined : specialty,
        city: city === "all" ? undefined : city,
        q: debouncedQ || undefined,
      })
      .then((d) => !ignore && setDoctors(d))
      .catch((e) => !ignore && setError(getErrorMessage(e, "Couldn't load doctors")));
    return () => {
      ignore = true;
    };
  }, [specialty, city, debouncedQ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Find a doctor</h1>
        <p className="text-muted-foreground">Browse specialists and book an appointment.</p>
      </div>

      {triageResultId && (
        <Alert>
          <AlertDescription>
            Showing specialists matched to your skin scan. Your booking will be linked to that result.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-3 sm:grid-cols-[1fr_220px_180px]">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name, specialty or hospital"
            className="pl-9"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <Select value={specialty} onValueChange={setSpecialty}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Specialty" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All specialties</SelectItem>
            {specialties.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={city} onValueChange={setCity}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="City" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All cities</SelectItem>
            {cities.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {doctors === null && !error ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      ) : doctors && doctors.length === 0 ? (
        <p className="py-12 text-center text-muted-foreground">No doctors match those filters.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {doctors?.map((d) => (
            <Card key={d.id} className="flex flex-col">
              <CardHeader className="space-y-2">
                <CardTitle className="text-lg">{d.name}</CardTitle>
                <Badge variant="secondary" className="w-fit">
                  {d.specialty}
                </Badge>
              </CardHeader>
              <CardContent className="flex-1 space-y-2 text-sm">
                <p className="font-medium">{d.hospital.name}</p>
                <p className="flex items-center gap-1 text-muted-foreground">
                  <MapPin className="size-3.5" /> {d.hospital.city}
                </p>
                {d.bio && <p className="line-clamp-2 text-muted-foreground">{d.bio}</p>}
              </CardContent>
              <CardFooter>
                <Button className="w-full" onClick={() => setSelected(d)}>
                  Book appointment
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      <BookingDialog
        key={selected?.id ?? "none"}
        doctor={selected}
        triageResultId={triageResultId}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
