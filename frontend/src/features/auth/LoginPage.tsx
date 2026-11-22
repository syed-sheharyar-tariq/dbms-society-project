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
    <div
      className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/assets/login-bg.png')" }}
    >
      {/* Dark overlay for contrast */}
      <div className="absolute inset-0 bg-slate-950/75 backdrop-blur-[2px]" />

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="h-14 w-14 rounded-2xl bg-emerald-500/90 border border-emerald-400/40 flex items-center justify-center font-bold text-white text-2xl mx-auto shadow-lg shadow-emerald-950/40">
          GS
        </div>
        <h2 className="mt-4 text-center text-2xl font-extrabold tracking-tight text-white drop-shadow-sm">
          Housing Society CMS
        </h2>
        <p className="mt-1 text-center text-xs font-medium text-emerald-300 drop-shadow-sm">
          Gulistan-e-Jauhar, Karachi • DBMS Project
        </p>
      </div>

      <div className="relative z-10 mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="backdrop-blur-md bg-slate-900/85 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-700/80 text-slate-100">
          {errorMsg && (
            <div className="mb-4 p-3 bg-red-950/70 border border-red-500/50 rounded-xl text-xs text-red-200 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3.5 py-2.5 bg-slate-800/90 border border-slate-600 rounded-xl text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all"
                placeholder="resident@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3.5 py-2.5 bg-slate-800/90 border border-slate-600 rounded-xl text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all disabled:opacity-50"
            >
              <LogIn className="h-4 w-4 mr-2" />
              {isSubmitting ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-5 text-center">
            <span className="text-xs text-slate-400">Don't have an account? </span>
            <Link to="/register" className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 underline underline-offset-2">
              Create an account
            </Link>
          </div>

          {/* Quick Demo Role Switcher */}
          <div className="mt-8 border-t border-slate-800 pt-6">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 text-center">
              Quick Role Preview & Verification
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickRole('resident')}
                className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-700/80 bg-slate-800/60 hover:bg-emerald-950/40 hover:border-emerald-500/60 text-xs font-medium text-slate-200 hover:text-emerald-300 transition-all"
              >
                <UserCheck className="h-4 w-4 text-emerald-400" />
                <span>Resident</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickRole('complaint_officer')}
                className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-700/80 bg-slate-800/60 hover:bg-amber-950/40 hover:border-amber-500/60 text-xs font-medium text-slate-200 hover:text-amber-300 transition-all"
              >
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                <span>Officer</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickRole('field_staff')}
                className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-700/80 bg-slate-800/60 hover:bg-indigo-950/40 hover:border-indigo-500/60 text-xs font-medium text-slate-200 hover:text-indigo-300 transition-all"
              >
                <Wrench className="h-4 w-4 text-indigo-400" />
                <span>Field Staff</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickRole('administrator')}
                className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-700/80 bg-slate-800/60 hover:bg-slate-700/60 hover:border-slate-500 text-xs font-medium text-slate-200 hover:text-white transition-all"
              >
                <ShieldCheck className="h-4 w-4 text-slate-300" />
                <span>Admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

