import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { StatusBadge } from '../../components/common/StatusBadge';
import {
  Clock,
  MapPin,
  RefreshCw,
  Wrench,
} from 'lucide-react';

export const StaffDashboard: React.FC = () => {
  const [assignments, setAssignments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Update status modal
  const [selectedAssignment, setSelectedAssignment] = useState<any | null>(null);
  const [targetStatus, setTargetStatus] = useState<string>('in_progress');
  const [notes, setNotes] = useState('');
  const [completionNotes, setCompletionNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadAssignments = async () => {
    setLoading(true);
    try {
      const res = await api.getAssignments();
      setAssignments(res.data.items || []);
    } catch (err) {
      console.error('Failed to load assignments', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignment) return;
    if (targetStatus === 'completed' && !completionNotes.trim()) {
      alert('Completion notes are required when marking work finished.');
      return;
    }

    setSubmitting(true);
    try {
      await api.updateAssignment(
        selectedAssignment.id,
        targetStatus,
        notes,
        targetStatus === 'completed' ? completionNotes : undefined
      );
      setSelectedAssignment(null);
      setNotes('');
      setCompletionNotes('');
      await loadAssignments();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to update assignment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Field Maintenance Assignments</h1>
          <p className="text-xs text-slate-500 mt-1">
            Society maintenance tasks allocated to you. Update progress and report completions.
          </p>
        </div>

        <button
          onClick={loadAssignments}
          className="text-slate-400 hover:text-slate-600 p-2 rounded-lg"
          title="Refresh"
        >
          <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="p-8 text-center text-slate-400 text-sm">Loading assignments...</div>
      ) : assignments.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-400">
          <Wrench className="h-10 w-10 mx-auto text-slate-300 mb-2" />
          <p className="text-sm font-medium text-slate-600">No active work assignments.</p>
          <p className="text-xs text-slate-400 mt-1">You are all caught up!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {assignments.map((a) => (
            <div key={a.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-900">{a.incident_number}</span>
                  <StatusBadge status={a.status} isUrgent={a.incident_priority === 'urgent' || a.incident_priority === 'emergency'} />
                </div>

                <h3 className="text-sm font-bold text-slate-900 mt-2">{a.incident_title}</h3>

                <div className="mt-3 space-y-1.5 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Wrench className="h-3.5 w-3.5 text-slate-400" />
                    <span>Category: <strong className="text-slate-700">{a.category_name}</strong></span>
                  </div>
                  {a.area_description && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" />
                      <span>Area: <strong className="text-slate-700">{a.area_description}</strong></span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    <span>Assigned: {new Date(a.assigned_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {a.completion_notes && (
                  <div className="mt-3 p-2.5 bg-emerald-50 text-emerald-800 rounded border border-emerald-100 text-xs">
                    <strong>Completion Notes:</strong> {a.completion_notes}
                  </div>
                )}
              </div>

              {a.status !== 'completed' && a.status !== 'cancelled' && (
                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center gap-2">
                  {a.status === 'assigned' && (
                    <button
                      onClick={() => {
                        setSelectedAssignment(a);
                        setTargetStatus('accepted');
                      }}
                      className="flex-1 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded transition-colors text-center"
                    >
                      Accept Task
                    </button>
                  )}

                  {(a.status === 'assigned' || a.status === 'accepted') && (
                    <button
                      onClick={() => {
                        setSelectedAssignment(a);
                        setTargetStatus('in_progress');
                      }}
                      className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded transition-colors text-center"
                    >
                      Start Work
                    </button>
                  )}

                  {a.status === 'in_progress' && (
                    <>
                      <button
                        onClick={() => {
                          setSelectedAssignment(a);
                          setTargetStatus('blocked');
                        }}
                        className="py-1.5 px-3 bg-amber-50 hover:bg-amber-100 text-amber-700 font-semibold text-xs rounded"
                      >
                        Report Blocker
                      </button>

                      <button
                        onClick={() => {
                          setSelectedAssignment(a);
                          setTargetStatus('completed');
                        }}
                        className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded text-center shadow-sm"
                      >
                        Finish Work
                      </button>
                    </>
                  )}

                  {a.status === 'blocked' && (
                    <button
                      onClick={() => {
                        setSelectedAssignment(a);
                        setTargetStatus('in_progress');
                      }}
                      className="flex-1 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded text-center"
                    >
                      Resume Work
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Progress / Status Update Modal */}
      {selectedAssignment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">
              Update Assignment Status: <span className="uppercase text-emerald-600">{targetStatus.replace('_', ' ')}</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">{selectedAssignment.incident_title}</p>

            <form onSubmit={handleUpdate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">
                  Progress Note / Reason
                </label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Need new replacement fuse / Work underway"
                  className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                />
              </div>

              {targetStatus === 'completed' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase">
                    Mandatory Completion Notes *
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={completionNotes}
                    onChange={(e) => setCompletionNotes(e.target.value)}
                    placeholder="Details of physical fix implemented (e.g. Replaced capacitor and tested line voltage)"
                    className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md text-xs"
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedAssignment(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : 'Submit Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
