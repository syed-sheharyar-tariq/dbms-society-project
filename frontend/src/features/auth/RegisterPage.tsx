import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../app/auth';
import { api } from '../../api/client';
import {
  UserPlus,
  AlertCircle,
  CheckCircle,
  Home,
  Wrench,
  Shield,
  PhoneCall,
  UserCheck,
} from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  // Common Fields
  const [role, setRole] = useState<'resident' | 'field_staff' | 'complaint_officer' | 'administrator'>('resident');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');

  // Resident Specifics
  const [blocks, setBlocks] = useState<any[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [selectedBlockId, setSelectedBlockId] = useState('');
  const [selectedPropertyId, setSelectedPropertyId] = useState('');
  const [relationshipType, setRelationshipType] = useState('owner');
  const [isNewProperty, setIsNewProperty] = useState(false);
  const [newPropertyNumber, setNewPropertyNumber] = useState('');

  // Staff Specifics
  const [tradeSpecialization, setTradeSpecialization] = useState('Electrician');

  // Officer Specifics
  const [badgeId, setBadgeId] = useState('CO-2026-01');
  const [deskLocation, setDeskLocation] = useState('Society Office - Desk 1');

  // Admin Specifics
  const [adminPasscode, setAdminPasscode] = useState('');

  // Submission State
  const [submitted, setSubmitted] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load Blocks & Properties on mount
  useEffect(() => {
    const loadMasterData = async () => {
      try {
        const bRes = await api.getBlocks();
        setBlocks(bRes.data || []);
        if (bRes.data?.length) {
          const firstBlockId = bRes.data[0].id;
          setSelectedBlockId(firstBlockId);
          const pRes = await api.getProperties(firstBlockId);
          setProperties(pRes.data || []);
          if (pRes.data?.length) {
            setSelectedPropertyId(pRes.data[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to load blocks/properties', err);
      }
    };
    loadMasterData();
  }, []);

  // Update properties when selected block changes
  const handleBlockChange = async (blockId: string) => {
    setSelectedBlockId(blockId);
    try {
      const pRes = await api.getProperties(blockId);
      setProperties(pRes.data || []);
      if (pRes.data?.length) {
        setSelectedPropertyId(pRes.data[0].id);
      } else {
        setSelectedPropertyId('');
      }
    } catch (err) {
      console.error('Failed to fetch properties for block', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (role === 'administrator' && adminPasscode !== 'society-admin-2026') {
      setErrorMsg('Invalid administrator security passcode. (Hint: society-admin-2026)');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await register({
        email,
        password,
        fullName,
        phone,
        role,
        tradeSpecialization: role === 'field_staff' ? tradeSpecialization : undefined,
        deskLocation: role === 'complaint_officer' ? deskLocation : undefined,
        badgeId: role === 'complaint_officer' ? badgeId : undefined,
        propertyId: role === 'resident' && !isNewProperty ? selectedPropertyId : undefined,
        blockId: role === 'resident' && isNewProperty ? selectedBlockId : undefined,
        newPropertyNumber: role === 'resident' && isNewProperty ? newPropertyNumber : undefined,
        relationshipType: role === 'resident' ? relationshipType : undefined,
        adminPasscode: role === 'administrator' ? adminPasscode : undefined,
      });

      if (res.session) {
        navigate('/');
      } else {
        setSubmitted(true);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.message || err.message || 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div
        className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/assets/login-bg.png')" }}
      >
        <div className="absolute inset-0 bg-slate-950/75 backdrop-blur-[2px]" />
        <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="backdrop-blur-md bg-slate-900/90 p-8 rounded-2xl shadow-2xl border border-slate-700/80 text-center text-white">
            <CheckCircle className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
            <h3 className="text-xl font-bold text-white">Registration Successful</h3>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">
              Your {role.replace('_', ' ')} account has been registered and initialized in the society database.
            </p>
            <p className="mt-2 text-xs text-slate-400">
              If Supabase email confirmation is enabled for your project, please verify your email link, or proceed directly to sign in with your credentials.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="mt-6 w-full py-2.5 px-4 rounded-xl font-semibold text-white bg-emerald-600 hover:bg-emerald-500 text-sm shadow-md transition-all"
            >
              Go to Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/assets/login-bg.png')" }}
    >
      <div className="absolute inset-0 bg-slate-950/75 backdrop-blur-[2px]" />

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-lg text-center">
        <div className="h-14 w-14 rounded-2xl bg-emerald-500/90 border border-emerald-400/40 flex items-center justify-center font-bold text-white text-2xl mx-auto shadow-lg shadow-emerald-950/40">
          GS
        </div>
        <h2 className="mt-4 text-center text-2xl font-extrabold tracking-tight text-white drop-shadow-sm">
          Society CMS Registration
        </h2>
        <p className="mt-1 text-center text-xs font-medium text-emerald-300 drop-shadow-sm">
          Gulistan-e-Jauhar, Karachi • Create Your Profile
        </p>
      </div>

      <div className="relative z-10 mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="backdrop-blur-md bg-slate-900/90 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-700/80 text-slate-100">
          {errorMsg && (
            <div className="mb-4 p-3 bg-red-950/70 border border-red-500/50 rounded-xl text-xs text-red-200 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Role Selection Tabs */}
          <div className="mb-6">
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              I am registering as:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => setRole('resident')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  role === 'resident'
                    ? 'bg-emerald-600/30 border-emerald-400 text-emerald-300 shadow-sm'
                    : 'bg-slate-800/70 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                <UserCheck className="h-4 w-4 mb-1" />
                <span>Resident</span>
              </button>

              <button
                type="button"
                onClick={() => setRole('field_staff')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  role === 'field_staff'
                    ? 'bg-indigo-600/30 border-indigo-400 text-indigo-300 shadow-sm'
                    : 'bg-slate-800/70 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Wrench className="h-4 w-4 mb-1" />
                <span>Field Staff</span>
              </button>

              <button
                type="button"
                onClick={() => setRole('complaint_officer')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  role === 'complaint_officer'
                    ? 'bg-amber-600/30 border-amber-400 text-amber-300 shadow-sm'
                    : 'bg-slate-800/70 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                <PhoneCall className="h-4 w-4 mb-1" />
                <span>Officer</span>
              </button>

              <button
                type="button"
                onClick={() => setRole('administrator')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  role === 'administrator'
                    ? 'bg-purple-600/30 border-purple-400 text-purple-300 shadow-sm'
                    : 'bg-slate-800/70 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Shield className="h-4 w-4 mb-1" />
                <span>Admin</span>
              </button>
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {/* Common Profile Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="mt-1 block w-full px-3.5 py-2 bg-slate-800/90 border border-slate-600 rounded-xl text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g. Tariq Khan"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="mt-1 block w-full px-3.5 py-2 bg-slate-800/90 border border-slate-600 rounded-xl text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="+92-300-1234567"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 block w-full px-3.5 py-2 bg-slate-800/90 border border-slate-600 rounded-xl text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="user@example.com"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 block w-full px-3.5 py-2 bg-slate-800/90 border border-slate-600 rounded-xl text-white placeholder-slate-400 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {/* Resident Role Specifics */}
            {role === 'resident' && (
              <div className="p-4 rounded-xl bg-slate-800/50 border border-emerald-500/30 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  <Home className="h-4 w-4" />
                  <span>Property & Occupancy Details</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-300">Society Block</label>
                    <select
                      value={selectedBlockId}
                      onChange={(e) => handleBlockChange(e.target.value)}
                      className="mt-1 block w-full px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs focus:ring-emerald-500"
                    >
                      {blocks.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name} ({b.code})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-slate-300">Occupancy Relationship</label>
                    <select
                      value={relationshipType}
                      onChange={(e) => setRelationshipType(e.target.value)}
                      className="mt-1 block w-full px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs focus:ring-emerald-500"
                    >
                      <option value="owner">Owner</option>
                      <option value="tenant">Tenant (On Rent)</option>
                      <option value="family_member">Family Member</option>
                      <option value="authorized_occupant">Authorized Occupant</option>
                    </select>
                  </div>
                </div>

                {!isNewProperty ? (
                  <div>
                    <div className="flex items-center justify-between">
                      <label className="block text-xs text-slate-300">Select Flat / House</label>
                      <button
                        type="button"
                        onClick={() => setIsNewProperty(true)}
                        className="text-[11px] text-emerald-400 hover:underline"
                      >
                        + Add new property unit
                      </button>
                    </div>
                    <select
                      value={selectedPropertyId}
                      onChange={(e) => setSelectedPropertyId(e.target.value)}
                      className="mt-1 block w-full px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs focus:ring-emerald-500"
                    >
                      {properties.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.property_number} ({p.property_type}) - {p.address_note || 'Standard unit'}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between">
                      <label className="block text-xs text-slate-300">New House / Flat Number</label>
                      <button
                        type="button"
                        onClick={() => setIsNewProperty(false)}
                        className="text-[11px] text-slate-400 hover:underline"
                      >
                        ← Choose existing
                      </button>
                    </div>
                    <input
                      type="text"
                      required={isNewProperty}
                      value={newPropertyNumber}
                      onChange={(e) => setNewPropertyNumber(e.target.value)}
                      placeholder="e.g. A-305 or House 42"
                      className="mt-1 block w-full px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs focus:ring-emerald-500"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Field Staff Specifics */}
            {role === 'field_staff' && (
              <div className="p-4 rounded-xl bg-slate-800/50 border border-indigo-500/30 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  <Wrench className="h-4 w-4" />
                  <span>Maintenance Trade Specialization</span>
                </div>

                <div>
                  <label className="block text-xs text-slate-300">Select Primary Trade</label>
                  <select
                    value={tradeSpecialization}
                    onChange={(e) => setTradeSpecialization(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:ring-indigo-500"
                  >
                    <option value="Electrician">Electrician (Wiring, Meters, Phase distribution)</option>
                    <option value="Plumber">Plumber (Water pipelines, Pumps, Valves, Leaks)</option>
                    <option value="Gas Technician">Gas Technician (Gas lines, Pressure regulation)</option>
                    <option value="Sewerage Worker">Sewerage & Sanitation Worker (Drainage, Manholes)</option>
                    <option value="HVAC Technician">HVAC / AC Technician (Common area cooling)</option>
                    <option value="Carpenter">Carpenter & General Masonry</option>
                    <option value="General Maintenance">General Society Handyman</option>
                  </select>
                </div>
              </div>
            )}

            {/* Complaint Officer Specifics */}
            {role === 'complaint_officer' && (
              <div className="p-4 rounded-xl bg-slate-800/50 border border-amber-500/30 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 uppercase tracking-wider">
                  <PhoneCall className="h-4 w-4" />
                  <span>Complaint Desk Credentials</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-300">Badge / Employee ID</label>
                    <input
                      type="text"
                      value={badgeId}
                      onChange={(e) => setBadgeId(e.target.value)}
                      className="mt-1 block w-full px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-slate-300">Office Desk Location</label>
                    <input
                      type="text"
                      value={deskLocation}
                      onChange={(e) => setDeskLocation(e.target.value)}
                      className="mt-1 block w-full px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Administrator Specifics */}
            {role === 'administrator' && (
              <div className="p-4 rounded-xl bg-slate-800/50 border border-purple-500/30 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-purple-400 uppercase tracking-wider">
                  <Shield className="h-4 w-4" />
                  <span>Administrative Security Key</span>
                </div>

                <div>
                  <label className="block text-xs text-slate-300">Admin Security Passcode</label>
                  <input
                    type="password"
                    required={role === 'administrator'}
                    value={adminPasscode}
                    onChange={(e) => setAdminPasscode(e.target.value)}
                    placeholder="Enter society administration passcode"
                    className="mt-1 block w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-xs"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Passcode is: <code className="text-purple-300 font-mono">society-admin-2026</code></p>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all disabled:opacity-50"
            >
              <UserPlus className="h-4 w-4 mr-2" />
              {isSubmitting ? 'Registering...' : `Register as ${role.replace('_', ' ')}`}
            </button>
          </form>

          <div className="mt-5 text-center">
            <span className="text-xs text-slate-400">Already registered? </span>
            <Link to="/login" className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 underline underline-offset-2">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
