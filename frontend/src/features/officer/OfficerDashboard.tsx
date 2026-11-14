import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { StatusBadge } from '../../components/common/StatusBadge';
import {
  AlertTriangle,
  CheckCircle2,
  Layers,
  PhoneCall,
  Truck,
  Wrench,
} from 'lucide-react';

export const OfficerDashboard: React.FC = () => {
  const [complaints, setComplaints] = useState<any[]>([]);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [utilities, setUtilities] = useState<any[]>([]);
  const [staffUsers, setStaffUsers] = useState<any[]>([]);

  // Filter state
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedComplaintIds, setSelectedComplaintIds] = useState<string[]>([]);

  // Create Incident Modal
  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [incidentTitle, setIncidentTitle] = useState('');
  const [incidentDesc, setIncidentDesc] = useState('');
  const [incidentCatId, setIncidentCatId] = useState('');
  const [incidentPriority, setIncidentPriority] = useState('normal');
  const [areaDesc, setAreaDesc] = useState('');

  // Assign Staff Modal
  const [assignIncidentId, setAssignIncidentId] = useState<string | null>(null);
  const [selectedStaffId, setSelectedStaffId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');

  // Lodge Utility Case Modal
  const [utilityIncidentId, setUtilityIncidentId] = useState<string | null>(null);
  const [selectedUtilityId, setSelectedUtilityId] = useState('');
  const [externalRef, setExternalRef] = useState('');
  const [expectedDueDate, setExpectedDueDate] = useState('');

  // Offline Intake Modal
  const [showOfflineModal, setShowOfflineModal] = useState(false);
  const [offlineResidentId, setOfflineResidentId] = useState('');
  const [offlinePropertyId, setOfflinePropertyId] = useState('');
  const [offlineCatId, setOfflineCatId] = useState('');
  const [offlineDesc, setOfflineDesc] = useState('');
  const [offlineChannel, setOfflineChannel] = useState('phone');
  const [offlineUrgent, setOfflineUrgent] = useState(false);
  const [offlineUrgentReason, setOfflineUrgentReason] = useState('');

  // Society properties & residents for offline intake
  const [properties, setProperties] = useState<any[]>([]);
  const [residents, setResidents] = useState<any[]>([]);

  const loadData = async () => {
    try {
      const [cRes, incRes, catRes, uRes, staffRes, pRes, rRes] = await Promise.all([
        api.getComplaints(),
        api.getIncidents(),
        api.getCategories(),
        api.getUtilityCompanies(),
        api.getUsers({ role: 'field_staff' }),
        api.getProperties(),
        api.getUsers({ role: 'resident' }),
      ]);
      setComplaints(cRes.data.items || []);
      setIncidents(incRes.data.items || []);
      setCategories(catRes.data || []);
      setUtilities(uRes.data || []);
      setStaffUsers(staffRes.data.items || []);
      setProperties(pRes.data || []);
      setResidents(rRes.data.items || []);

      if (catRes.data?.length) {
        setIncidentCatId(catRes.data[0].id);
        setOfflineCatId(catRes.data[0].id);
      }
      if (staffRes.data.items?.length) {
        setSelectedStaffId(staffRes.data.items[0].id);
      }
      if (uRes.data?.length) {
        setSelectedUtilityId(uRes.data[0].id);
      }
      if (pRes.data?.length) {
        setOfflinePropertyId(pRes.data[0].id);
      }
      if (rRes.data.items?.length) {
        setOfflineResidentId(rRes.data.items[0].id);
      }
    } catch (err) {
      console.error('Failed to load officer dashboard data', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGroupIntoIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createIncident({
        title: incidentTitle,
        description: incidentDesc,
        category_id: incidentCatId,
        priority: incidentPriority,
        area_description: areaDesc,
        complaint_ids: selectedComplaintIds,
      });
      setShowIncidentModal(false);
      setSelectedComplaintIds([]);
      setIncidentTitle('');
      setIncidentDesc('');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to create incident');
    }
  };

  const handleAssignStaff = async () => {
    if (!assignIncidentId || !selectedStaffId) return;
    try {
      await api.assignStaff(assignIncidentId, selectedStaffId, assignNotes);
      setAssignIncidentId(null);
      setAssignNotes('');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to assign staff');
    }
  };

  const handleLodgeUtility = async () => {
    if (!utilityIncidentId || !selectedUtilityId) return;
    try {
      await api.createUtilityCase(utilityIncidentId, {
        utility_company_id: selectedUtilityId,
        external_reference_number: externalRef || undefined,
        expected_resolution_at: expectedDueDate ? new Date(expectedDueDate).toISOString() : undefined,
      });
      setUtilityIncidentId(null);
      setExternalRef('');
      setExpectedDueDate('');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to lodge utility case');
    }
  };

  const handleRecordOffline = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createOfflineComplaint({
        resident_id: offlineResidentId,
        property_id: offlinePropertyId,
        category_id: offlineCatId,
        description: offlineDesc,
        is_urgent: offlineUrgent,
        urgency_reason: offlineUrgent ? offlineUrgentReason : undefined,
        intake_channel: offlineChannel,
      });
      setShowOfflineModal(false);
      setOfflineDesc('');
      setOfflineUrgent(false);
      setOfflineUrgentReason('');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to record offline complaint');
    }
  };

  const handleResolveIncident = async (incidentId: string) => {
    const reason = prompt('Enter resolution summary / physical repair report:');
    if (!reason) return;
    try {
      await api.updateIncidentStatus(incidentId, 'resolved', reason);
      alert('Incident marked resolved! All eligible linked complaints moved to Pending Confirmation.');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to update incident status');
    }
  };

  const toggleSelectComplaint = (id: string) => {
    setSelectedComplaintIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const urgentComplaints = complaints.filter((c) => c.is_urgent && c.status !== 'closed' && c.status !== 'cancelled');

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Complaint Officer Operations</h1>
          <p className="text-xs text-slate-500 mt-1">
            Triage complaints, group shared faults into incidents, dispatch internal staff, and coordinate external utilities.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {selectedComplaintIds.length > 0 && (
            <button
              onClick={() => setShowIncidentModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Layers className="h-4 w-4" />
              <span>Group ({selectedComplaintIds.length}) into Incident</span>
            </button>
          )}

          <button
            onClick={() => setShowOfflineModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <PhoneCall className="h-4 w-4" />
            <span>Record Offline Intake</span>
          </button>
        </div>
      </div>

      {/* Urgent Safety Issues Alert Box (AT-18, PR-09) */}
      {urgentComplaints.length > 0 && (
        <div className="bg-rose-50 border-2 border-rose-300 p-5 rounded-xl shadow-sm">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-rose-600 shrink-0 animate-bounce" />
            <div>
              <h3 className="text-sm font-bold text-rose-900">
                CRITICAL SAFETY ESCALATIONS ({urgentComplaints.length})
              </h3>
              <p className="text-xs text-rose-700 mt-0.5">
                Gas leakage or electrical sparking reports requiring immediate operational attention.
              </p>
            </div>
          </div>
          <div className="mt-3 space-y-2">
            {urgentComplaints.map((uc) => (
              <div key={uc.id} className="bg-white p-3 rounded-lg border border-rose-200 flex items-center justify-between text-xs">
                <div>
                  <span className="font-mono font-bold text-rose-950">{uc.complaint_number}</span>
                  <span className="ml-2 font-semibold text-slate-700">{uc.category_name}</span>
                  <span className="ml-2 text-slate-500">Property: {uc.property_number}</span>
                  <p className="text-slate-800 mt-0.5 font-medium">{uc.description}</p>
                  {uc.urgency_reason && <p className="text-rose-600 italic">Hazard: {uc.urgency_reason}</p>}
                </div>
                <StatusBadge status={uc.status} isUrgent={true} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Triage & Complaints Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2">
            <h2 className="font-bold text-slate-800 text-sm">Complaint Triage Queue</h2>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-semibold">
              {complaints.length} Total
            </span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs border border-slate-300 rounded-md px-2 py-1.5 text-slate-700"
            >
              <option value="">All Statuses</option>
              <option value="submitted">Submitted</option>
              <option value="under_review">Under Review</option>
              <option value="in_progress">In Progress</option>
              <option value="pending_confirmation">Pending Confirmation</option>
              <option value="closed">Closed</option>
              <option value="reopened">Reopened</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
            <thead className="bg-slate-50 font-semibold text-slate-600">
              <tr>
                <th className="p-3 w-10 text-center">Select</th>
                <th className="p-3">Complaint #</th>
                <th className="p-3">Category</th>
                <th className="p-3">Property</th>
                <th className="p-3">Intake</th>
                <th className="p-3">Status</th>
                <th className="p-3">Linked Incident</th>
                <th className="p-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {complaints.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3 text-center">
                    <input
                      type="checkbox"
                      checked={selectedComplaintIds.includes(c.id)}
                      onChange={() => toggleSelectComplaint(c.id)}
                      className="rounded border-slate-300 text-emerald-600"
                    />
                  </td>
                  <td className="p-3 font-mono font-bold text-slate-900">{c.complaint_number}</td>
                  <td className="p-3 font-medium text-slate-700">{c.category_name}</td>
                  <td className="p-3 text-slate-600">{c.property_number || 'A-101'}</td>
                  <td className="p-3 uppercase font-mono text-[10px] text-slate-500">{c.intake_channel}</td>
                  <td className="p-3">
                    <StatusBadge status={c.status} isUrgent={c.is_urgent} />
                  </td>
                  <td className="p-3">
                    {c.active_incident_number ? (
                      <span className="font-mono font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                        {c.active_incident_number}
                      </span>
                    ) : (
                      <span className="text-slate-400 italic">Unassigned</span>
                    )}
                  </td>
                  <td className="p-3 text-slate-400 font-mono text-[11px]">
                    {new Date(c.submitted_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incidents Management Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-600" />
            <h2 className="font-bold text-slate-800 text-sm">Active Society Incidents</h2>
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {incidents.map((inc) => (
            <div key={inc.id} className="p-6 hover:bg-slate-50 transition-colors">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold text-sm text-slate-900">{inc.incident_number}</span>
                  <StatusBadge status={inc.status} />
                  <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                    Routing: {inc.routing_type}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {inc.status !== 'resolved' && inc.status !== 'closed' && (
                    <>
                      <button
                        onClick={() => setAssignIncidentId(inc.id)}
                        className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold flex items-center gap-1"
                      >
                        <Wrench className="h-3.5 w-3.5" />
                        <span>Assign Staff</span>
                      </button>

                      <button
                        onClick={() => setUtilityIncidentId(inc.id)}
                        className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold flex items-center gap-1"
                      >
                        <Truck className="h-3.5 w-3.5" />
                        <span>Lodge Utility</span>
                      </button>

                      <button
                        onClick={() => handleResolveIncident(inc.id)}
                        className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1 shadow-sm"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Mark Resolved</span>
                      </button>
                    </>
                  )}
                </div>
              </div>

              <h3 className="text-sm font-bold text-slate-900 mt-2">{inc.title}</h3>
              <p className="text-xs text-slate-600 mt-1">{inc.description}</p>

              <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
                <span>Category: <strong className="text-slate-700">{inc.category_name}</strong></span>
                <span>Linked Complaints: <strong className="text-slate-700">{inc.linked_complaint_count}</strong></span>
                {inc.area_description && <span>Area: <strong className="text-slate-700">{inc.area_description}</strong></span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Group Complaints into Incident Modal */}
      {showIncidentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900">Group Complaints into Shared Incident</h3>
            <p className="text-xs text-slate-500 mt-1">
              Grouping {selectedComplaintIds.length} complaints into a single operational incident.
            </p>

            <form onSubmit={handleGroupIntoIncident} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Incident Title</label>
                <input
                  type="text"
                  required
                  value={incidentTitle}
                  onChange={(e) => setIncidentTitle(e.target.value)}
                  placeholder="e.g. Block A Water Pump Failure"
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Category</label>
                <select
                  value={incidentCatId}
                  onChange={(e) => setIncidentCatId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                  required
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Priority</label>
                <select
                  value={incidentPriority}
                  onChange={(e) => setIncidentPriority(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Description</label>
                <textarea
                  rows={3}
                  required
                  value={incidentDesc}
                  onChange={(e) => setIncidentDesc(e.target.value)}
                  placeholder="Explain the root problem affecting multiple flats..."
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Area / Location Description</label>
                <input
                  type="text"
                  value={areaDesc}
                  onChange={(e) => setAreaDesc(e.target.value)}
                  placeholder="e.g., Underground pump room near Block A entrance"
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowIncidentModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-md text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-semibold"
                >
                  Create & Link Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Staff Dialog */}
      {assignIncidentId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Assign Field Staff</h3>
            <p className="text-xs text-slate-500 mt-1">Allocate work assignment to active society staff.</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Select Staff Member</label>
                <select
                  value={selectedStaffId}
                  onChange={(e) => setSelectedStaffId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  {staffUsers.map((s) => (
                    <option key={s.id} value={s.id}>{s.full_name} ({s.phone || 'Staff'})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Assignment Instructions</label>
                <textarea
                  rows={3}
                  value={assignNotes}
                  onChange={(e) => setAssignNotes(e.target.value)}
                  placeholder="Specific task instructions..."
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAssignIncidentId(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded-md text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleAssignStaff}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold"
                >
                  Dispatch Staff
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lodge Utility Case Dialog */}
      {utilityIncidentId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Route to External Utility Provider</h3>
            <p className="text-xs text-slate-500 mt-1">Lodge tracking case with K-Electric, SSGC, or Water Board.</p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Utility Company</label>
                <select
                  value={selectedUtilityId}
                  onChange={(e) => setSelectedUtilityId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                >
                  {utilities.map((u) => (
                    <option key={u.id} value={u.id}>{u.name} ({u.contact_phone})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Provider External Reference #</label>
                <input
                  type="text"
                  value={externalRef}
                  onChange={(e) => setExternalRef(e.target.value)}
                  placeholder="e.g. KE-998811"
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Expected Due Date</label>
                <input
                  type="datetime-local"
                  value={expectedDueDate}
                  onChange={(e) => setExpectedDueDate(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setUtilityIncidentId(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded-md text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleLodgeUtility}
                  className="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-xs font-semibold"
                >
                  Save Utility Case
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Offline Intake Registration Modal (PR-12) */}
      {showOfflineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Record Offline Complaint (Walk-in / Phone / WhatsApp)</h3>
            <p className="text-xs text-slate-500 mt-1">Official intake for resident complaints received outside the portal.</p>

            <form onSubmit={handleRecordOffline} className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase">Intake Channel</label>
                  <select
                    value={offlineChannel}
                    onChange={(e) => setOfflineChannel(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                  >
                    <option value="phone">Phone Call</option>
                    <option value="whatsapp">WhatsApp</option>
                    <option value="office_visit">Office Walk-In</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase">Category</label>
                  <select
                    value={offlineCatId}
                    onChange={(e) => setOfflineCatId(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Resident Account</label>
                <select
                  value={offlineResidentId}
                  onChange={(e) => setOfflineResidentId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                  required
                >
                  {residents.map((r) => (
                    <option key={r.id} value={r.id}>{r.full_name} ({r.email})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Affected Property</label>
                <select
                  value={offlinePropertyId}
                  onChange={(e) => setOfflinePropertyId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                  required
                >
                  {properties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.block_name || 'Block'} - {p.property_number} ({p.property_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Description</label>
                <textarea
                  rows={3}
                  required
                  value={offlineDesc}
                  onChange={(e) => setOfflineDesc(e.target.value)}
                  placeholder="Details given by the resident..."
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                />
              </div>

              <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={offlineUrgent}
                    onChange={(e) => setOfflineUrgent(e.target.checked)}
                    className="h-4 w-4 text-rose-600 rounded border-slate-300"
                  />
                  <span className="text-xs font-bold text-rose-900">
                    Flag Urgent Safety Issue (Gas Leak / Electrical Sparking)
                  </span>
                </label>
                {offlineUrgent && (
                  <input
                    type="text"
                    required
                    value={offlineUrgentReason}
                    onChange={(e) => setOfflineUrgentReason(e.target.value)}
                    placeholder="Urgency reason (e.g. Smell of gas near main line)"
                    className="mt-2 block w-full px-2.5 py-1 text-xs border border-rose-300 rounded"
                  />
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowOfflineModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold"
                >
                  Save Offline Complaint
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
