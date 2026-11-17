import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "@/hooks/useAuth";
import { dashboardPath } from "@/lib/roles";
import type { Role } from "@/types";

export function FullPageLoader() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center text-muted-foreground">
      Loading...
    </div>
  );
}

/** Must be logged in (and, if roles given, have one of them). */
export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <FullPageLoader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={dashboardPath(user.role)} replace />;
  }
  return <Outlet />;
}

/** Login/register: logged-in users get bounced to their dashboard. */
export function PublicOnlyRoute() {
  const { user, loading } = useAuth();
  if (loading) return <FullPageLoader />;
  if (user) return <Navigate to={dashboardPath(user.role)} replace />;
  return <Outlet />;
}
