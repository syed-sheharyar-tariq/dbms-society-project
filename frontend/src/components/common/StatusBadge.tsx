import React from 'react';

interface StatusBadgeProps {
  status: string;
  isUrgent?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, isUrgent }) => {
  const getColors = () => {
    switch (status.toLowerCase()) {
      case 'submitted':
      case 'open':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'under_review':
      case 'triaged':
      case 'assigned':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'in_progress':
      case 'accepted':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'awaiting_external':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'pending_confirmation':
        return 'bg-orange-50 text-orange-700 border-orange-300 font-semibold animate-pulse';
      case 'resolved':
      case 'completed':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'closed':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'reopened':
        return 'bg-rose-50 text-rose-700 border-rose-300 font-semibold';
      case 'blocked':
        return 'bg-red-50 text-red-700 border-red-300 font-semibold';
      case 'cancelled':
        return 'bg-slate-100 text-slate-500 border-slate-200';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const formatText = (text: string) => {
    return text.replace(/_/g, ' ').toUpperCase();
  };

  return (
    <div className="inline-flex items-center gap-1.5">
      <span className={`px-2.5 py-0.5 text-xs rounded-full border ${getColors()}`}>
        {formatText(status)}
      </span>
      {isUrgent && (
        <span className="px-2 py-0.5 text-xs rounded-full bg-rose-600 text-white font-bold tracking-wide animate-bounce shadow-sm">
          URGENT
        </span>
      )}
    </div>
  );
};
