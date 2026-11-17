import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/errors";
import { adminService } from "@/services/admin";
import type { AdminStats, Role, User } from "@/types";

const ROLES: Role[] = ["patient", "doctor", "admin"];

function StatCard({ label, value, hint }: { label: string; value: number | undefined; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl">{value ?? <Skeleton className="h-8 w-12" />}</CardTitle>
      </CardHeader>
      {hint && <CardContent className="text-xs text-muted-foreground">{hint}</CardContent>}
    </Card>
  );
}

export default function AdminDashboard() {
  const { user: me } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, u] = await Promise.all([adminService.stats(), adminService.users()]);
      setStats(s);
      setUsers(u);
    } catch (e) {
      setError(getErrorMessage(e, "Couldn't load admin data"));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function update(u: User, patch: { role?: Role; is_active?: boolean }) {
    setSavingId(u.id);
    try {
      const updated = await adminService.updateUser(u.id, patch);
      setUsers((list) => list?.map((x) => (x.id === updated.id ? updated : x)) ?? null);
      toast.success(`Updated ${updated.name}`);
      adminService.stats().then(setStats).catch(() => {});
    } catch (e) {
      toast.error(getErrorMessage(e, "Update failed"));
    } finally {
      setSavingId(null);
    }
  }

  const a = stats?.appointments_by_status;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Admin dashboard</h1>
        <p className="text-muted-foreground">Platform overview and user management</p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Patients" value={stats?.users_by_role.patient} />
        <StatCard
          label="Doctor accounts"
          value={stats?.users_by_role.doctor}
          hint={stats ? `${stats.doctors} in directory` : undefined}
        />
        <StatCard label="Hospitals" value={stats?.hospitals} />
        <StatCard label="Skin scans" value={stats?.triage_results} hint="Available after Phase 3" />
        <StatCard label="Active bookings" value={a ? a.booked + a.confirmed : undefined} />
        <StatCard label="Completed" value={a?.completed} />
        <StatCard label="Cancelled" value={a?.cancelled} />
        <StatCard label="Active accounts" value={stats?.active_users} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
          <CardDescription>Change roles or disable accounts. You can't demote or disable yourself.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {users === null ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => {
                    const isMe = u.id === me?.id;
                    const busy = savingId === u.id;
                    return (
                      <TableRow key={u.id}>
                        <TableCell>
                          <div className="font-medium">
                            {u.name} {isMe && <span className="text-xs text-muted-foreground">(you)</span>}
                          </div>
                          <div className="text-xs text-muted-foreground">{u.email}</div>
                        </TableCell>
                        <TableCell>
                          <Select
                            value={u.role}
                            disabled={isMe || busy}
                            onValueChange={(v) => void update(u, { role: v as Role })}
                          >
                            <SelectTrigger className="w-32 capitalize">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {ROLES.map((r) => (
                                <SelectItem key={r} value={r} className="capitalize">
                                  {r}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          {u.is_active ? (
                            <Badge variant="secondary">Active</Badge>
                          ) : (
                            <Badge variant="destructive">Disabled</Badge>
                          )}
                        </TableCell>
                        <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                          {new Date(u.created_at).toLocaleDateString("en-IN")}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={isMe || busy}
                            onClick={() => void update(u, { is_active: !u.is_active })}
                          >
                            {u.is_active ? "Disable" : "Enable"}
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
