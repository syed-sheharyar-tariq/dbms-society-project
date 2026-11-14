import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import {
  RefreshCw,
  TrendingUp,
  Truck,
  Wrench,
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [summary, setSummary] = useState<any | null>(null);
  const [recurringFaults, setRecurringFaults] = useState<any[]>([]);
  const [staffWorkload, setStaffWorkload] = useState<any[]>([]);
  const [utilityPerformance, setUtilityPerformance] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadReports = async () => {
    setLoading(true);
    try {
      const [sumRes, recRes, staffRes, utilRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getRecurringFaults(90),
        api.getStaffWorkload(),
        api.getUtilityPerformance(),
      ]);
      setSummary(sumRes.data);
      setRecurringFaults(recRes.data || []);
      setStaffWorkload(staffRes.data || []);
      setUtilityPerformance(utilRes.data || []);
    } catch (err) {
      console.error('Failed to load reports', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Executive Society Analytics & KPIs</h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time operational metrics, recurring fault trends, staff utilization, and utility performance.
          </p>
        </div>

        <button
          onClick={loadReports}
          className="p-2 text-slate-400 hover:text-slate-600 rounded-lg"
          title="Refresh Metrics"
        >
          <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* KPI Metric Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">New Complaints</span>
            <span className="text-2xl font-black text-blue-600 mt-1 block">{summary.new_complaints_count}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Awaiting review</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Active Pending</span>
            <span className="text-2xl font-black text-indigo-600 mt-1 block">{summary.pending_complaints_count}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Not closed/cancelled</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Open Incidents</span>
            <span className="text-2xl font-black text-purple-600 mt-1 block">{summary.open_incidents_count}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Shared fault clusters</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Pending Resident</span>
            <span className="text-2xl font-black text-orange-600 mt-1 block">{summary.pending_confirmations_count}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Awaiting sign-off</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Overdue Utility</span>
            <span className="text-2xl font-black text-rose-600 mt-1 block">{summary.overdue_utility_cases_count}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Past due date</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Urgent Safety</span>
            <span className="text-2xl font-black text-rose-700 mt-1 block">{summary.urgent_open_items_count}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Gas / sparking wire</span>
          </div>
        </div>
      )}

      {/* Grid: Recurring Faults & Staff Workload */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recurring Fault Trends (PR-11, Section 12.2) */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-purple-600" />
              <h2 className="font-bold text-slate-800 text-sm">Recurring Fault Patterns (90 Days)</h2>
            </div>
            <span className="text-xs text-slate-400">Advisory Indicator</span>
          </div>

          <div className="p-6 flex-1">
            {recurringFaults.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-8">No recurring fault clusters detected.</p>
            ) : (
              <div className="space-y-3">
                {recurringFaults.map((rf, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-xs text-slate-900">
                        {rf.block_name} • {rf.category_name}
                      </div>
                      {rf.area_description && (
                        <div className="text-[11px] text-slate-500">{rf.area_description}</div>
                      )}
                    </div>
                    <span className="px-2.5 py-1 bg-purple-100 text-purple-800 text-xs font-bold rounded-full font-mono">
                      {rf.incident_count} Incidents
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Staff Workload Distribution (Section 12.4) */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wrench className="h-4 w-4 text-emerald-600" />
              <h2 className="font-bold text-slate-800 text-sm">Staff Workload Distribution</h2>
            </div>
          </div>

          <div className="p-6 flex-1">
            {staffWorkload.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-8">No active assignments on staff.</p>
            ) : (
              <div className="space-y-3">
                {staffWorkload.map((sw) => (
                  <div key={sw.staff_profile_id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-xs text-slate-900 block">{sw.staff_name}</span>
                      <span className="text-[11px] text-slate-400">
                        Assigned: {sw.assigned_count} • In Progress: {sw.in_progress_count} • Blocked: {sw.blocked_count}
                      </span>
                    </div>
                    <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full font-mono">
                      {sw.total_active} Active
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* External Utility Performance (Section 12.3) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Truck className="h-4 w-4 text-indigo-600" />
            <h2 className="font-bold text-slate-800 text-sm">External Utility Response Times</h2>
          </div>
          <span className="text-xs text-slate-400">K-Electric • SSGC • Water Board</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
            <thead className="bg-slate-50 font-semibold text-slate-600">
              <tr>
                <th className="p-3">Utility Organization</th>
                <th className="p-3">Total Cases</th>
                <th className="p-3">Response Sample Count</th>
                <th className="p-3">Avg First Response Latency</th>
                <th className="p-3">Avg Resolution Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {utilityPerformance.map((u) => (
                <tr key={u.utility_company_id} className="hover:bg-slate-50">
                  <td className="p-3 font-semibold text-slate-900">{u.utility_name}</td>
                  <td className="p-3 font-mono">{u.total_cases}</td>
                  <td className="p-3 font-mono">{u.sample_count}</td>
                  <td className="p-3 text-slate-600">
                    {u.avg_first_response_hours !== null && u.avg_first_response_hours !== undefined
                      ? `${u.avg_first_response_hours.toFixed(1)} hrs`
                      : 'Awaiting data'}
                  </td>
                  <td className="p-3 text-slate-600">
                    {u.avg_resolution_hours !== null && u.avg_resolution_hours !== undefined
                      ? `${u.avg_resolution_hours.toFixed(1)} hrs`
                      : 'Awaiting data'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
