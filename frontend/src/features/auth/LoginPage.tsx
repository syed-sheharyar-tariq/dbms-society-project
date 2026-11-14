import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../app/auth';
import { ShieldCheck, UserCheck, Wrench, AlertTriangle, LogIn } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, setDemoSession } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick Role Simulator (Generates verified demo token & profile)
  const handleQuickRole = (role: 'resident' | 'complaint_officer' | 'field_staff' | 'administrator') => {
    // Generate valid mock JWT payload format
    const demoToken = 'demo-token-' + role;
    const demoProfiles = {
      resident: {
        id: '11111111-1111-1111-1111-111111111111',
        auth_user_id: 'a1111111-1111-1111-1111-111111111111',
        role: 'resident' as const,
        full_name: 'Fahad Resident (Flat A-204)',
        email: 'resident@jauhar.com',
        is_active: true,
      },
      complaint_officer: {
        id: '22222222-2222-2222-2222-222222222222',
        auth_user_id: 'a2222222-2222-2222-2222-222222222222',
        role: 'complaint_officer' as const,
        full_name: 'Tariq Mehmood (Complaint Officer)',
        email: 'officer@jauhar.com',
        is_active: true,
      },
      field_staff: {
        id: '33333333-3333-3333-3333-333333333333',
        auth_user_id: 'a3333333-3333-3333-3333-333333333333',
        role: 'field_staff' as const,
        full_name: 'Imran Khan (Society Electrician)',
        email: 'staff@jauhar.com',
        is_active: true,
      },
      administrator: {
        id: '44444444-4444-4444-4444-444444444444',
        auth_user_id: 'a4444444-4444-4444-4444-444444444444',
        role: 'administrator' as const,
        full_name: 'Society Administrator',
        email: 'admin@jauhar.com',
        is_active: true,
      },
    };

    const residentInfo = role === 'resident' ? {
      id: '55555555-5555-5555-5555-555555555555',
      profile_id: demoProfiles.resident.id,
      verification_status: 'verified' as const,
      properties: [
        {
          property_id: '66666666-6666-6666-6666-666666666666',
          property_number: 'A-204',
          block_code: 'BLK-A',
          relationship_type: 'owner',
          is_primary_contact: true,
        }
      ]
    } : undefined;

    setDemoSession(role, demoToken, demoProfiles[role], residentInfo);
    navigate('/');
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="h-12 w-12 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white text-xl mx-auto shadow-md">
          GS
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-slate-900">
          Housing Society CMS
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          Gulistan-e-Jauhar, Karachi • DBMS Project
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl shadow-slate-200/50 sm:rounded-xl sm:px-10 border border-slate-200">
          {errorMsg && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm text-sm focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="resident@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm text-sm focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-colors disabled:opacity-50"
            >
              <LogIn className="h-4 w-4 mr-2" />
              {isSubmitting ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-4 text-center">
            <span className="text-xs text-slate-500">Don't have an account? </span>
            <Link to="/register" className="text-xs font-semibold text-emerald-600 hover:text-emerald-700">
              Register as Resident
            </Link>
          </div>

          {/* Quick Demo Role Switcher */}
          <div className="mt-8 border-t border-slate-200 pt-6">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 text-center">
              Quick Role Preview & Smoke Testing
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickRole('resident')}
                className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-300 text-xs font-medium text-slate-700 hover:text-emerald-800 transition-colors"
              >
                <UserCheck className="h-4 w-4 text-emerald-600" />
                <span>Resident</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickRole('complaint_officer')}
                className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-amber-50 hover:border-amber-300 text-xs font-medium text-slate-700 hover:text-amber-800 transition-colors"
              >
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <span>Officer</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickRole('field_staff')}
                className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-indigo-50 hover:border-indigo-300 text-xs font-medium text-slate-700 hover:text-indigo-800 transition-colors"
              >
                <Wrench className="h-4 w-4 text-indigo-600" />
                <span>Field Staff</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickRole('administrator')}
                className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-200 hover:border-slate-400 text-xs font-medium text-slate-700 hover:text-slate-900 transition-colors"
              >
                <ShieldCheck className="h-4 w-4 text-slate-700" />
                <span>Admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
