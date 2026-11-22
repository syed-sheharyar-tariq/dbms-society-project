import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import {
  Home,
  Plus,
  RefreshCw,
  Shield,
  Users,
  Building,
} from 'lucide-react';


export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'properties' | 'audit'>('properties');
  const [users, setUsers] = useState<any[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [occupancy, setOccupancy] = useState<any[]>([]);
  const [blocks, setBlocks] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Property Resident Association Modal
  const [showAssocModal, setShowAssocModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [assocPropertyId, setAssocPropertyId] = useState('');
  const [relationType, setRelationType] = useState('owner');
  const [validFromDate, setValidFromDate] = useState(new Date().toISOString().split('T')[0]);

  // Create Property Modal
  const [showCreatePropModal, setShowCreatePropModal] = useState(false);
  const [newPropBlockId, setNewPropBlockId] = useState('');
  const [newPropNumber, setNewPropNumber] = useState('');
  const [newPropType, setNewPropType] = useState('flat');
  const [newPropNote, setNewPropNote] = useState('');
  const [creatingProp, setCreatingProp] = useState(false);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [uRes, pRes, aRes, occRes, bRes] = await Promise.all([
        api.getUsers(),
        api.getProperties(),
        api.getAuditLogs(),
        api.getPropertyOccupancy(),
        api.getBlocks(),
      ]);
      setUsers(uRes.data.items || []);
      setProperties(pRes.data || []);
      setAuditLogs(aRes.data.items || []);
      setOccupancy(occRes.data || []);
      setBlocks(bRes.data || []);

      if (uRes.data.items?.length) {
        setSelectedUserId(uRes.data.items[0].id);
      }
      if (pRes.data?.length) {
        setAssocPropertyId(pRes.data[0].id);
      }
      if (bRes.data?.length) {
        setNewPropBlockId(bRes.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load admin data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleVerifyResident = async (profileId: string, outcome: 'verified' | 'rejected') => {
    try {
      await api.verifyResident(profileId, outcome);
      alert(`Resident verification updated to: ${outcome}`);
      await loadAdminData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Verification update failed');
    }
  };

  const handleRoleChange = async (profileId: string, newRole: string) => {
    if (!confirm(`Are you sure you want to change user role to ${newRole}?`)) return;
    try {
      await api.updateUserRole(profileId, newRole);
      await loadAdminData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Role change failed');
    }
  };

  const handleCreateAssociation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.associatePropertyResident({
        resident_id: selectedUserId,
        property_id: assocPropertyId,
        relationship_type: relationType,
        valid_from: validFromDate,
      });
      setShowAssocModal(false);
      alert('Property association recorded successfully!');
      await loadAdminData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Association failed');
    }
  };

  const handleCreateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingProp(true);
    try {
      await api.createProperty({
        block_id: newPropBlockId,
        property_number: newPropNumber,
        property_type: newPropType,
        address_note: newPropNote,
      });
      setShowCreatePropModal(false);
      setNewPropNumber('');
      setNewPropNote('');
      alert('Property created successfully!');
      await loadAdminData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to create property');
    } finally {
      setCreatingProp(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Society Administration</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage society properties, monitor resident ownership/tenancy directory, and audit all mutations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreatePropModal(true)}
            className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Create Property</span>
          </button>
          <button
            onClick={() => setShowAssocModal(true)}
            className="px-3 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-colors"
          >
            <Home className="h-4 w-4" />
            <span>Link Resident</span>
          </button>
          <button
            onClick={loadAdminData}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 space-x-4">
        <button
          onClick={() => setActiveTab('properties')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-1.5 border-b-2 ${
            activeTab === 'properties'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-400 hover:text-slate-700'
          }`}
        >
          <Building className="h-4 w-4" />
          <span>Properties & Occupancy Directory ({occupancy.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-1.5 border-b-2 ${
            activeTab === 'users'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-400 hover:text-slate-700'
          }`}
        >
          <Users className="h-4 w-4" />
          <span>User Profiles & Verification ({users.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-1.5 border-b-2 ${
            activeTab === 'audit'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-400 hover:text-slate-700'
          }`}
        >
          <Shield className="h-4 w-4" />
          <span>Append-Only Audit Trail</span>
        </button>
      </div>

      {/* TAB 1: Properties & Occupancy Directory */}
      {activeTab === 'properties' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="font-bold text-slate-800 text-sm">Society Property Occupancy Directory</h2>
              <p className="text-[11px] text-slate-500">
                Complete overview of who owns each unit, who is currently residing on rent/lease, and active fault counts.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
              <thead className="bg-slate-50 font-semibold text-slate-600">
                <tr>
                  <th className="p-3">Unit Number</th>
                  <th className="p-3">Block</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Registered Owner</th>
                  <th className="p-3">Current Residents / Tenants</th>
                  <th className="p-3">Active Issues</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {occupancy.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="p-3 font-bold font-mono text-slate-900">{p.property_number}</td>
                    <td className="p-3 text-slate-700">{p.block_name || p.block_code}</td>
                    <td className="p-3 capitalize text-slate-600">{p.property_type}</td>
                    <td className="p-3">
                      {p.owner ? (
                        <div>
                          <div className="font-semibold text-slate-900">{p.owner.full_name}</div>
                          {p.owner.phone && <div className="text-[10px] text-slate-500">{p.owner.phone}</div>}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">No registered owner</span>
                      )}
                    </td>
                    <td className="p-3">
                      {p.occupants?.length ? (
                        <div className="space-y-1">
                          {p.occupants.map((occ: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-1.5">
                              <span className="font-medium text-slate-800">{occ.full_name}</span>
                              <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 capitalize">
                                {occ.relationship_type.replace('_', ' ')}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Vacant / Unoccupied</span>
                      )}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        p.active_complaints_count > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {p.active_complaints_count} open
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        p.occupancy_status === 'Occupied' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {p.occupancy_status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => {
                          setAssocPropertyId(p.id);
                          setShowAssocModal(true);
                        }}
                        className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded text-[11px] font-semibold transition-colors"
                      >
                        + Link Resident
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: Users & Verification */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="font-bold text-slate-800 text-sm">Registered Profiles & Roles</h2>
              <p className="text-[11px] text-slate-500">
                Verify resident accounts to authorize complaint submissions, or update organizational roles.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
              <thead className="bg-slate-50 font-semibold text-slate-600">
                <tr>
                  <th className="p-3">Full Name</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Phone</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="p-3 font-semibold text-slate-900">{u.full_name}</td>
                    <td className="p-3 text-slate-600">{u.email}</td>
                    <td className="p-3 text-slate-500">{u.phone || '—'}</td>
                    <td className="p-3 font-semibold uppercase text-[11px] text-indigo-700">
                      {u.role.replace('_', ' ')}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {u.role === 'resident' && (
                          <button
                            onClick={() => handleVerifyResident(u.id, 'verified')}
                            className="px-2 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded text-[11px] font-semibold"
                            title="Verify Resident Property Occupancy"
                          >
                            Verify
                          </button>
                        )}
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          className="border border-slate-300 rounded px-2 py-1 text-xs"
                        >
                          <option value="resident">Resident</option>
                          <option value="field_staff">Field Staff</option>
                          <option value="complaint_officer">Complaint Officer</option>
                          <option value="administrator">Administrator</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Audit Log Trail (AT-21) */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-slate-700" />
              <h2 className="font-bold text-slate-800 text-sm">Append-Only System Audit Trail</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">Immutable Log</span>
          </div>

          <div className="overflow-x-auto max-h-96">
            <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
              <thead className="bg-slate-50 font-semibold text-slate-600 sticky top-0">
                <tr>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Actor</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Entity Type</th>
                  <th className="p-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="p-3 text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
                    <td className="p-3 font-sans font-medium text-slate-800">{log.actor_name || 'System'}</td>
                    <td className="p-3 font-bold text-indigo-700">{log.action}</td>
                    <td className="p-3 text-slate-600 uppercase text-[10px]">{log.entity_type}</td>
                    <td className="p-3 text-slate-500 max-w-xs truncate">
                      {log.new_values ? JSON.stringify(log.new_values) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Create Property */}
      {showCreatePropModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Create New Society Property</h3>
            <p className="text-xs text-slate-500 mt-1">
              Add a new house or apartment unit across any society block.
            </p>

            <form onSubmit={handleCreateProperty} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Block</label>
                <select
                  value={newPropBlockId}
                  onChange={(e) => setNewPropBlockId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                  required
                >
                  {blocks.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Property Unit Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. A-301 or House 55"
                  value={newPropNumber}
                  onChange={(e) => setNewPropNumber(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Property Type</label>
                <select
                  value={newPropType}
                  onChange={(e) => setNewPropType(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  <option value="flat">Flat / Apartment</option>
                  <option value="house">House / Bungalow</option>
                  <option value="other">Commercial / Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Address Notes / Floor</label>
                <input
                  type="text"
                  placeholder="e.g. 3rd Floor Park View"
                  value={newPropNote}
                  onChange={(e) => setNewPropNote(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreatePropModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingProp}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold"
                >
                  {creatingProp ? 'Creating...' : 'Create Property'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Link Resident to Property */}
      {showAssocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Authorize Resident Property Occupancy</h3>
            <p className="text-xs text-slate-500 mt-1">
              Associate a verified resident with their house/flat to permit complaint lodgement.
            </p>

            <form onSubmit={handleCreateAssociation} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Resident User</label>
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.email || u.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Society Property</label>
                <select
                  value={assocPropertyId}
                  onChange={(e) => setAssocPropertyId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  {properties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.block_name || 'Block'} - {p.property_number} ({p.property_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Relationship Type</label>
                <select
                  value={relationType}
                  onChange={(e) => setRelationType(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  <option value="owner">Owner</option>
                  <option value="tenant">Tenant (On Rent)</option>
                  <option value="family_member">Family Member</option>
                  <option value="authorized_occupant">Authorized Occupant</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Valid From</label>
                <input
                  type="date"
                  value={validFromDate}
                  onChange={(e) => setValidFromDate(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAssocModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold"
                >
                  Grant Property Access
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
