import React from 'react';
import { CaseStatus } from '../types';
import { Clock, CheckCircle2, Archive } from 'lucide-react';

interface Props {
  status: CaseStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<Props> = ({ status, size = 'md' }) => {
  const isSm = size === 'sm';
  
  if (status === 'pending_claim') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 ${
          isSm ? 'px-2.5 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'
        }`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
        <Clock className="w-3.5 h-3.5" />
        <span>Pending Claim</span>
      </span>
    );
  }

  if (status === 'active') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${
          isSm ? 'px-2.5 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'
        }`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        <CheckCircle2 className="w-3.5 h-3.5" />
        <span>Active Recovery</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/30 ${
        isSm ? 'px-2.5 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'
      }`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
      <Archive className="w-3.5 h-3.5" />
      <span>Closed</span>
    </span>
  );
};
