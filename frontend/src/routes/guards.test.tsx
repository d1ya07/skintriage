import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";
import { AuthContext, type AuthContextValue } from "@/context/auth-context";
import type { User } from "@/types";
import { ProtectedRoute } from "./guards";

const patient: User = {
  id: 1,
  name: "Pat",
  email: "p@example.com",
  role: "patient",
  is_active: true,
  skin_type: null,
  created_at: "2026-01-01T00:00:00Z",
};

function renderAt(path: string, user: User | null) {
  const value: AuthContextValue = {
    user,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  };
  render(
    <AuthContext.Provider value={value}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/login" element={<p>login page</p>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/patient" element={<p>patient home</p>} />
          </Route>
          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="/admin" element={<p>admin home</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("sends logged-out users to login", () => {
    renderAt("/patient", null);
    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("lets a logged-in patient in", () => {
    renderAt("/patient", patient);
    expect(screen.getByText("patient home")).toBeInTheDocument();
  });

  it("bounces a patient away from admin pages", () => {
    renderAt("/admin", patient);
    expect(screen.queryByText("admin home")).not.toBeInTheDocument();
    expect(screen.getByText("patient home")).toBeInTheDocument();
  });
});
