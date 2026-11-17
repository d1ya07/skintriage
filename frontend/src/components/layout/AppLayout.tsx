import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { toast } from "sonner";
import { Disclaimer } from "@/components/Disclaimer";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/useAuth";
import { dashboardPath } from "@/lib/roles";
import { cn } from "@/lib/utils";
import type { Role } from "@/types";

const LINKS_BY_ROLE: Record<Role, { to: string; label: string }[]> = {
  patient: [
    { to: "/patient", label: "Dashboard" },
    { to: "/scan", label: "Skin scan" },
    { to: "/doctors", label: "Find a doctor" },
    { to: "/appointments", label: "My appointments" },
  ],
  doctor: [{ to: "/doctor", label: "Dashboard" }],
  admin: [{ to: "/admin", label: "Dashboard" }],
};

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;

  const initials = user.name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const links = [...LINKS_BY_ROLE[user.role], { to: "/profile", label: "Profile" }];

  async function handleLogout() {
    await logout();
    toast.success("Logged out");
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/30">
      <header className="border-b bg-background">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <Link to={dashboardPath(user.role)} className="text-lg font-semibold">
              🩺 SkinTriage
            </Link>
            <nav className="hidden gap-1 md:flex">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  className={({ isActive }) =>
                    cn(
                      "rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground",
                      isActive && "bg-muted font-medium text-foreground",
                    )
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2">
                <Avatar className="size-7">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
                <span className="hidden sm:inline">{user.name}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="space-y-1">
                <div className="truncate text-sm">{user.email}</div>
                <Badge variant="secondary" className="capitalize">
                  {user.role}
                </Badge>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {links.map((l) => (
                <DropdownMenuItem key={l.to} onSelect={() => navigate(l.to)}>
                  {l.label}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={handleLogout}>Log out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t bg-background px-4 py-4">
        <Disclaimer />
      </footer>
    </div>
  );
}
