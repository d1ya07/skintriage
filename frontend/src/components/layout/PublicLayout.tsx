import { Link, Outlet } from "react-router";
import { Disclaimer } from "@/components/Disclaimer";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { dashboardPath } from "@/lib/roles";

export function PublicLayout() {
  const { user } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="text-lg font-semibold">
            🩺 SkinTriage
          </Link>
          <nav className="flex gap-2">
            {user ? (
              <Button asChild>
                <Link to={dashboardPath(user.role)}>Go to dashboard</Link>
              </Button>
            ) : (
              <>
                <Button variant="ghost" asChild>
                  <Link to="/login">Log in</Link>
                </Button>
                <Button asChild>
                  <Link to="/register">Sign up</Link>
                </Button>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4">
        <Outlet />
      </main>
      <footer className="border-t py-4 px-4">
        <Disclaimer />
      </footer>
    </div>
  );
}
