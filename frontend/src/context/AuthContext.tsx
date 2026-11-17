import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { AUTH_LOGOUT_EVENT, tokenStorage } from "@/services/api";
import { authService } from "@/services/auth";
import type { RegisterPayload, User } from "@/types";
import { AuthContext } from "./auth-context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!tokenStorage.get()) {
      setUser(null);
      return;
    }
    try {
      setUser(await authService.me());
    } catch {
      tokenStorage.clear();
      setUser(null);
    }
  }, []);

  // Restore session on first load (e.g. after a page refresh).
  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  // The axios interceptor fires this when the token expires.
  useEffect(() => {
    const onLogout = () => setUser(null);
    window.addEventListener(AUTH_LOGOUT_EVENT, onLogout);
    return () => window.removeEventListener(AUTH_LOGOUT_EVENT, onLogout);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const u = await authService.login(email, password);
    setUser(u);
    return u;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const u = await authService.register(payload);
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
