import { BrowserRouter, Routes, Route } from "react-router-dom";
import LoginPage from "../features/auth/LoginPage";
import RegisterPage from "../features/auth/RegisterPage";
import DashboardPage from "../pages/DashboardPage";
import EventPage from "../pages/EventPage";
import GuestsPage from "../pages/GuestsPage";
import TablesPage from "../pages/TablesPage";
import InvitationsPage from "../pages/InvitationsPage";
import FinancesPage from "../pages/FinancesPage";
import AccountPage from "../pages/AccountPage";
import LandingPage from "../pages/LandingPage";
import ProtectedRoute from "./ProtectedRoute";
import Layout from "../components/layout/Layout";

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedLayout>
              <DashboardPage />
            </ProtectedLayout>
          }
        />
        <Route
          path="/event"
          element={
            <ProtectedLayout>
              <EventPage />
            </ProtectedLayout>
          }
        />
        <Route
          path="/guests"
          element={
            <ProtectedLayout>
              <GuestsPage />
            </ProtectedLayout>
          }
        />
        <Route
          path="/tables"
          element={
            <ProtectedLayout>
              <TablesPage />
            </ProtectedLayout>
          }
        />
        <Route
          path="/invitations"
          element={
            <ProtectedLayout>
              <InvitationsPage />
            </ProtectedLayout>
          }
        />
        <Route
          path="/finances"
          element={
            <ProtectedLayout>
              <FinancesPage />
            </ProtectedLayout>
          }
        />
        <Route
          path="/account"
          element={
            <ProtectedLayout>
              <AccountPage />
            </ProtectedLayout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}