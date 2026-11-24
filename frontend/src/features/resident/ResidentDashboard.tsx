import React, { useEffect, useState } from 'react';
import { useAuth } from '../../app/auth';
import { api } from '../../api/client';
import { StatusBadge } from '../../components/common/StatusBadge';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  PlusCircle,
  RefreshCw,
  XCircle,
  FileText,
} from 'lucide-react';

export const ResidentDashboard: React.FC = () => {
  const { profile, resident } = useAuth();
  const [complaints, setComplaints] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [properties, setProperties] = useState<any[]>([]);
  const [authorizedProperties, setAuthorizedProperties] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);


  // New Complaint Form State
  const [showModal, setShowModal] = useState(false);
  const [propertyId, setPropertyId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [isUrgent, setIsUrgent] = useState(false);
  const [urgencyReason, setUrgencyReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  // Confirmation Modal State
  const [confirmModalComplaint, setConfirmModalComplaint] = useState<any | null>(null);
  const [feedback, setFeedback] = useState('');
  const [confirming, setConfirming] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cRes, catRes, pRes, meRes] = await Promise.all([
        api.getComplaints(),
        api.getCategories(),
        api.getProperties(),
        api.me().catch(() => null),
      ]);
      setComplaints(cRes.data.items || []);
      setCategories(catRes.data || []);
      setProperties(pRes.data || []);

      const liveProps = meRes?.data?.resident?.properties || resident?.properties || [];
      setAuthorizedProperties(liveProps);

      if (liveProps.length > 0) {
        setPropertyId(liveProps[0].property_id);
      } else if (pRes.data?.length) {
        setPropertyId(pRes.data[0].id);
      }
      if (catRes.data?.length) {
        setCategoryId(catRes.data[0].id);
      }
    } catch (err) {
      console.error('Error fetching resident dashboard data', err);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadData();
  }, [resident]);

  const handleCreateComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!description.trim()) {
      setFormError('Please describe the problem.');
      return;
    }
    setSubmitting(true);
    try {
      await api.createComplaint({
        property_id: propertyId,
        category_id: categoryId,
        description,
        is_urgent: isUrgent,
        urgency_reason: isUrgent ? urgencyReason : undefined,
      });
      setShowModal(false);
      setDescription('');
      setIsUrgent(false);
      setUrgencyReason('');
      await loadData();
    } catch (err: any) {
      setFormError(err.response?.data?.message || 'Failed to submit complaint.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolutionResponse = async (outcome: 'confirmed' | 'rejected') => {
    if (!confirmModalComplaint) return;
    setConfirming(true);
    try {
      await api.confirmComplaintResolution(confirmModalComplaint.id, outcome, feedback);
      setConfirmModalComplaint(null);
      setFeedback('');
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to submit confirmation.');
    } finally {
      setConfirming(false);
    }
  };

  const pendingConfirmations = complaints.filter((c) => c.status === 'pending_confirmation');

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Action */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Resident Portal</h1>
          <p className="text-xs text-slate-500 mt-1">
            Welcome, {profile?.full_name}. Manage and track your residential complaints.
          </p>
        </div>

        <button
          onClick={() => {
            const currentProps = authorizedProperties.length > 0 ? authorizedProperties : (resident?.properties || []);
            if (currentProps.length > 0) {
              setPropertyId(currentProps[0].property_id);
            }
            setShowModal(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold text-sm shadow-sm transition-colors"
        >
          <PlusCircle className="h-4 w-4" />
          <span>New Complaint</span>
        </button>

      </div>

      {/* Pending Confirmations Alert (PR-10) */}
      {pendingConfirmations.length > 0 && (
        <div className="bg-orange-50 border-2 border-orange-300 p-5 rounded-xl">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-orange-600 shrink-0" />
            <div>
              <h3 className="text-sm font-bold text-orange-900">
                Action Required: {pendingConfirmations.length} Complaint(s) Pending Your Confirmation
              </h3>
              <p className="text-xs text-orange-700 mt-0.5">
                Work has been reported resolved by society maintenance. Please inspect and confirm or reject resolution.
              </p>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {pendingConfirmations.map((c) => (
              <div key={c.id} className="bg-white p-3.5 rounded-lg border border-orange-200 flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs font-bold text-slate-800">{c.complaint_number}</span>
                  <span className="text-xs text-slate-500 ml-2">• {c.category_name}</span>
                  <p className="text-xs text-slate-700 mt-1">{c.description}</p>
                </div>
                <button
                  onClick={() => setConfirmModalComplaint(c)}
                  className="px-3 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
                >
                  Review & Confirm
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Complaints List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-bold text-slate-800 text-sm">My Registered Complaints</h2>
          <button
            onClick={loadData}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Loading complaints...</div>
        ) : complaints.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <FileText className="h-10 w-10 mx-auto text-slate-300 mb-2" />
            <p className="text-sm font-medium text-slate-600">No complaints registered yet.</p>
            <p className="text-xs text-slate-400 mt-1">Submit your first complaint using the button above.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {complaints.map((c) => (
              <div key={c.id} className="p-6 hover:bg-slate-50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-sm text-slate-900">{c.complaint_number}</span>
                    <StatusBadge status={c.status} isUrgent={c.is_urgent} />
                  </div>
                  <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                    <Clock className="h-3.5 w-3.5" />
                    {new Date(c.submitted_at).toLocaleString()}
                  </span>
                </div>

                <div className="mt-3 text-xs text-slate-500 flex items-center gap-4">
                  <span>Category: <strong className="text-slate-700">{c.category_name}</strong></span>
                  <span>Property: <strong className="text-slate-700">{c.property_number || 'A-101'}</strong></span>
                  {c.active_incident_number && (
                    <span className="text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded font-mono font-semibold">
                      Linked to: {c.active_incident_number}
                    </span>
                  )}
                </div>

                <p className="mt-2 text-sm text-slate-800 leading-relaxed">{c.description}</p>
                {c.urgency_reason && (
                  <div className="mt-2 text-xs text-rose-700 bg-rose-50 p-2 rounded border border-rose-100">
                    <strong>Urgency Reason:</strong> {c.urgency_reason}
                  </div>
                )}

                {/* 4-Step Lifecycle Visual Stepper */}
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500 mb-1.5">
                    <span>Workflow Progress</span>
                    <span className="capitalize font-mono font-bold text-slate-700">Current: {c.status.replace('_', ' ')}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                    <div className={`p-1.5 rounded text-center text-[10px] font-bold ${
                      ['submitted', 'under_review', 'in_progress', 'pending_confirmation', 'closed'].includes(c.status)
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      1. Submitted (Office Triage)
                    </div>
                    <div className={`p-1.5 rounded text-center text-[10px] font-bold ${
                      ['under_review', 'in_progress', 'pending_confirmation', 'closed'].includes(c.status)
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      2. Staff Working on Fix
                    </div>
                    <div className={`p-1.5 rounded text-center text-[10px] font-bold ${
                      c.status === 'pending_confirmation'
                        ? 'bg-orange-100 text-orange-900 border-2 border-orange-400 font-extrabold shadow-sm'
                        : ['closed'].includes(c.status)
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      3. Action: Resident Approval
                    </div>
                    <div className={`p-1.5 rounded text-center text-[10px] font-bold ${
                      c.status === 'closed'
                        ? 'bg-emerald-600 text-white'
                        : c.status === 'reopened'
                        ? 'bg-amber-600 text-white'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      4. {c.status === 'reopened' ? 'Reopened' : 'Resolved & Closed'}
                    </div>
                  </div>
                </div>

              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Complaint Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 border border-slate-200">
            <h2 className="text-lg font-bold text-slate-900">Lodge New Society Complaint</h2>
            <p className="text-xs text-slate-500 mt-1">
              Complaints are triaged by society complaint officers and dispatched to internal staff or external utilities.
            </p>

            {formError && (
              <div className="mt-3 p-3 bg-red-50 text-red-600 text-xs rounded-lg border border-red-200">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateComplaint} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Property / House / Flat</label>
                <select
                  value={propertyId}
                  onChange={(e) => setPropertyId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                  required
                >
                  {(authorizedProperties.length > 0 ? authorizedProperties : (resident?.properties || [])).length > 0 ? (
                    (authorizedProperties.length > 0 ? authorizedProperties : resident!.properties).map((rp) => (
                      <option key={rp.property_id} value={rp.property_id}>
                        Unit {rp.property_number} ({rp.relationship_type}) — Authorized
                      </option>
                    ))
                  ) : (
                    properties.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.block_name || 'Block'} - {p.property_number} ({p.property_type})
                      </option>
                    ))
                  )}

                </select>

              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Category</label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                  required
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Problem Description</label>
                <textarea
                  rows={4}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the fault clearly..."
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              {/* Safety Urgency Flag (PR-09) */}
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isUrgent}
                    onChange={(e) => setIsUrgent(e.target.checked)}
                    className="h-4 w-4 text-rose-600 rounded border-slate-300"
                  />
                  <span className="text-xs font-bold text-rose-900">
                    Mark as Urgent Safety Hazard (Gas Leakage / Sparking Wire)
                  </span>
                </label>
                {isUrgent && (
                  <input
                    type="text"
                    required
                    value={urgencyReason}
                    onChange={(e) => setUrgencyReason(e.target.value)}
                    placeholder="Provide urgency reason (e.g., active sparking outside meter)"
                    className="mt-2 block w-full px-3 py-1.5 border border-rose-300 rounded text-xs bg-white text-rose-900"
                  />
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 rounded-md text-xs font-semibold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-semibold disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Lodge Complaint'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resident Confirmation / Rejection Modal (PR-10) */}
      {confirmModalComplaint && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Confirm Resolution</h3>
            <p className="text-xs text-slate-500 mt-1">
              Complaint <strong className="font-mono text-slate-800">{confirmModalComplaint.complaint_number}</strong>
            </p>

            <div className="my-4 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-700">
              <p className="font-semibold text-slate-900 mb-1">Reported Fault:</p>
              <p>{confirmModalComplaint.description}</p>
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-700 uppercase">
                Feedback / Notes (Optional)
              </label>
              <textarea
                rows={3}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Was the work done properly? Any remaining issues?"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
              />
            </div>

            <div className="mt-6 flex flex-col sm:flex-row gap-2">
              <button
                type="button"
                disabled={confirming}
                onClick={() => handleResolutionResponse('confirmed')}
                className="flex-1 inline-flex justify-center items-center gap-1.5 py-2.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
              >
                <CheckCircle className="h-4 w-4" />
                <span>Confirm & Close</span>
              </button>

              <button
                type="button"
                disabled={confirming}
                onClick={() => handleResolutionResponse('rejected')}
                className="flex-1 inline-flex justify-center items-center gap-1.5 py-2.5 px-3 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors"
              >
                <XCircle className="h-4 w-4" />
                <span>Reject & Reopen</span>
              </button>
            </div>

            <button
              onClick={() => setConfirmModalComplaint(null)}
              className="mt-3 w-full py-1 text-center text-xs text-slate-400 hover:text-slate-600"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
