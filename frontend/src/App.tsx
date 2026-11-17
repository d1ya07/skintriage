import { BrowserRouter, Route, Routes } from "react-router";
import { ChatWidget } from "@/components/chat/ChatWidget";
import { AppLayout } from "@/components/layout/AppLayout";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { AuthProvider } from "@/context/AuthContext";
import AdminDashboard from "@/pages/AdminDashboard";
import AppointmentsPage from "@/pages/AppointmentsPage";
import DoctorDashboard from "@/pages/DoctorDashboard";
import DoctorsPage from "@/pages/DoctorsPage";
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import NotFoundPage from "@/pages/NotFoundPage";
import PatientDashboard from "@/pages/PatientDashboard";
import ProfilePage from "@/pages/ProfilePage";
import RegisterPage from "@/pages/RegisterPage";
import ScanPage from "@/pages/ScanPage";
import ScanResultPage from "@/pages/ScanResultPage";
import { ProtectedRoute, PublicOnlyRoute } from "@/routes/guards";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public pages */}
          <Route element={<PublicLayout />}>
            <Route index element={<LandingPage />} />
            <Route element={<PublicOnlyRoute />}>
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Route>

          {/* Logged-in pages */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="profile" element={<ProfilePage />} />
              <Route element={<ProtectedRoute roles={["patient"]} />}>
                <Route path="patient" element={<PatientDashboard />} />
                <Route path="doctors" element={<DoctorsPage />} />
                <Route path="appointments" element={<AppointmentsPage />} />
                <Route path="scan" element={<ScanPage />} />
                <Route path="scan/:id" element={<ScanResultPage />} />
              </Route>
              <Route element={<ProtectedRoute roles={["doctor"]} />}>
                <Route path="doctor" element={<DoctorDashboard />} />
              </Route>
              <Route element={<ProtectedRoute roles={["admin"]} />}>
                <Route path="admin" element={<AdminDashboard />} />
              </Route>
            </Route>
          </Route>
        </Routes>
        <ChatWidget />
      </AuthProvider>
    </BrowserRouter>
  );
}
