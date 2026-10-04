import React from 'react';
import { Case } from '../types';
import { FolderCheck, Clock, Camera, Radio } from 'lucide-react';

interface Props {
  cases: Case[];
  currentTenantId?: string;
  totalSightingsCount?: number;
}

export const MetricCards: React.FC<Props> = ({
  cases,
  currentTenantId,
  totalSightingsCount = 0,
}) => {
  const activeCasesCount = cases.filter(
    (c) => c.tenant_id === currentTenantId && c.status === 'active'
  ).length;

  const pendingClaimsCount = cases.filter((c) => c.status === 'pending_claim').length;

  const closedCasesCount = cases.filter(
    (c) => c.tenant_id === currentTenantId && c.status === 'closed'
  ).length;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Metric 1: Active Cases */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg relative overflow-hidden group hover:border-slate-700 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Active Agency Cases
          </span>
          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
            <FolderCheck className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">{activeCasesCount}</span>
          <span className="text-xs text-emerald-400 font-medium">Under active recovery</span>
        </div>
        <div className="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
          <div
            className="bg-emerald-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(activeCasesCount * 25, 100)}%` }}
          />
        </div>
      </div>

      {/* Metric 2: Pending Claims */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg relative overflow-hidden group hover:border-amber-500/30 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Claimable Network Pool
          </span>
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
            <Clock className="w-4 h-4 animate-spin-slow" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-amber-400">{pendingClaimsCount}</span>
          <span className="text-xs text-amber-300 font-medium">Eligible for claim</span>
        </div>
        <div className="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
          <div
            className="bg-amber-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(pendingClaimsCount * 30, 100)}%` }}
          />
        </div>
      </div>

      {/* Metric 3: Fleet Camera Stream */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg relative overflow-hidden group hover:border-slate-700 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Truck Camera Status
          </span>
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
            <Camera className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">ONLINE</span>
          <span className="text-xs text-indigo-400 flex items-center gap-1 font-medium">
            <Radio className="w-3 h-3 animate-pulse" />
            Ingesting OCR
          </span>
        </div>
        <div className="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
          <div className="bg-indigo-500 h-full rounded-full w-full" />
        </div>
      </div>

      {/* Metric 4: Closed / Historical Recoveries */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-lg relative overflow-hidden group hover:border-slate-700 transition">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Resolved Recoveries
          </span>
          <div className="p-2 rounded-xl bg-slate-700/30 text-slate-400">
            <FolderCheck className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono text-white">{closedCasesCount}</span>
          <span className="text-xs text-slate-400 font-medium">Archived cases</span>
        </div>
        <div className="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
          <div
            className="bg-slate-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(closedCasesCount * 20, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};
