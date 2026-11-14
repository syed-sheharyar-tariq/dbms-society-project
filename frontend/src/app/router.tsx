import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth';
import { AppLayout } from '../components/layout/AppLayout';
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';
import { ResidentDashboard } from '../features/resident/ResidentDashboard';
import { OfficerDashboard } from '../features/officer/OfficerDashboard';
import { StaffDashboard } from '../features/staff/StaffDashboard';
import { AdminDashboard } from '../features/admin/AdminDashboard';
import { ReportsPage } from '../features/reports/ReportsPage';

const ProtectedRoute: React.FC<{
  allowedRoles: string[];
  children: React.ReactNode;
}> = ({ allowedRoles, children }) => {
  const { profile, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-400 text-sm">
        Authenticating session...
      </div>
    );
  }

  if (!profile) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(profile.role)) {
    // Redirect to permitted landing for this user's role
    if (profile.role === 'resident') return <Navigate to="/resident" replace />;
    if (profile.role === 'complaint_officer') return <Navigate to="/officer" replace />;
    if (profile.role === 'field_staff') return <Navigate to="/staff" replace />;
    if (profile.role === 'administrator') return <Navigate to="/admin" replace />;
    return <Navigate to="/login" replace />;
  }

  return <AppLayout>{children}</AppLayout>;
};

const RootRedirect: React.FC = () => {
  const { profile, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-400 text-sm">
        Loading society portal...
      </div>
    );
  }

  if (!profile) return <Navigate to="/login" replace />;
  if (profile.role === 'resident') return <Navigate to="/resident" replace />;
  if (profile.role === 'complaint_officer') return <Navigate to="/officer" replace />;
  if (profile.role === 'field_staff') return <Navigate to="/staff" replace />;
  if (profile.role === 'administrator') return <Navigate to="/admin" replace />;
  return <Navigate to="/login" replace />;
};

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/resident"
          element={
            <ProtectedRoute allowedRoles={['resident']}>
              <ResidentDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/officer"
          element={
            <ProtectedRoute allowedRoles={['complaint_officer', 'administrator']}>
              <OfficerDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/staff"
          element={
            <ProtectedRoute allowedRoles={['field_staff']}>
              <StaffDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['administrator']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/reports"
          element={
            <ProtectedRoute allowedRoles={['complaint_officer', 'administrator']}>
              <ReportsPage />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
