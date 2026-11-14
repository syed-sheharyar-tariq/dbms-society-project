import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/auth';
import {
  AlertTriangle,
  BarChart3,
  FileText,
  LogOut,
  Users,
  Wrench,
} from 'lucide-react';

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { profile, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    // Resident routes
    { path: '/resident', label: 'My Complaints', icon: FileText, roles: ['resident'] },
    // Officer routes
    { path: '/officer', label: 'Triage & Incidents', icon: AlertTriangle, roles: ['complaint_officer', 'administrator'] },
    // Staff routes
    { path: '/staff', label: 'My Assignments', icon: Wrench, roles: ['field_staff'] },
    // Admin routes
    { path: '/admin', label: 'Society & Users', icon: Users, roles: ['administrator'] },
    // Reports routes
    { path: '/reports', label: 'Analytics & KPIs', icon: BarChart3, roles: ['complaint_officer', 'administrator'] },
  ];

  const allowedNav = navItems.filter((item) => profile && item.roles.includes(profile.role));

  const formatRole = (role?: string) => {
    if (!role) return '';
    return role.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Top Header */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow-inner">
              GS
            </div>
            <div>
              <span className="font-semibold text-base sm:text-lg tracking-tight block">
                Gulistan-e-Jauhar Society
              </span>
              <span className="text-xs text-slate-400 block -mt-1 font-mono">
                Complaint Management System
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {profile && (
              <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-slate-200">{profile.full_name}</div>
                <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                  {formatRole(profile.role)}
                </div>
              </div>
            )}

            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md transition-colors border border-slate-700"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 gap-6">
        {/* Navigation Sidebar */}
        <aside className="w-56 shrink-0 hidden md:block">
          <nav className="space-y-1 sticky top-24">
            {allowedNav.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Dynamic Content Pane */}
        <main className="flex-1 min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
};
