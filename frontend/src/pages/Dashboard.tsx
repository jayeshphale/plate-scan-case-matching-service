import React, { useState, useEffect, useCallback } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { casesApi } from '../api/cases';
import { Case } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { MetricCards } from '../components/MetricCards';
import { ClaimModal } from '../components/ClaimModal';
import {
  FolderOpen,
  Clock,
  Search,
  RefreshCw,
  Eye,
  CheckCircle,
  AlertTriangle,
  Building2,
  Car,
  Copy,
  Check,
  ExternalLink,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { refreshTrigger } = useOutletContext<{ refreshTrigger: number }>();

  const [activeTab, setActiveTab] = useState<'myCases' | 'pendingClaims'>('myCases');
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters & Search
  const [vinSearch, setVinSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [copiedVin, setCopiedVin] = useState<string | null>(null);

  // Claim modal state
  const [claimingCase, setClaimingCase] = useState<Case | null>(null);

  const fetchCases = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const params: any = { page_size: 50 };
      if (vinSearch.trim()) {
        params.vin = vinSearch.trim();
      }
      if (activeTab === 'pendingClaims') {
        params.status = 'pending_claim';
      } else if (statusFilter) {
        params.status = statusFilter;
      }

      const response = await casesApi.getCases(params);
      setCases(response.items);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to fetch cases from server.');
    } finally {
      setLoading(false);
    }
  }, [activeTab, vinSearch, statusFilter]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases, refreshTrigger, user?.tenant_id]);

  const handleClaimSuccess = (updatedCase: Case) => {
    fetchCases();
    setActiveTab('myCases');
  };

  const handleCopy = (vin: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(vin);
    setCopiedVin(vin);
    setTimeout(() => setCopiedVin(null), 1800);
  };

  // Partition cases
  const myAgencyCases = cases.filter(
    (c) => c.tenant_id === user?.tenant_id && c.status !== 'pending_claim'
  );
  const pendingCases = cases.filter((c) => c.status === 'pending_claim');

  const displayedCases = activeTab === 'myCases' ? myAgencyCases : pendingCases;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Telemetry Metric Cards */}
      <MetricCards cases={cases} currentTenantId={user?.tenant_id} />

      {/* Control Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        {/* Segmented Tab Buttons */}
        <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900 border border-slate-800">
          <button
            onClick={() => {
              setActiveTab('myCases');
              setStatusFilter('');
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === 'myCases'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>My Agency Cases</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
              activeTab === 'myCases' ? 'bg-indigo-800 text-indigo-100' : 'bg-slate-800 text-slate-400'
            }`}>
              {myAgencyCases.length}
            </span>
          </button>

          <button
            onClick={() => {
              setActiveTab('pendingClaims');
              setStatusFilter('');
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === 'pendingClaims'
                ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Pending Claims Pool</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
              activeTab === 'pendingClaims' ? 'bg-amber-800 text-amber-100' : 'bg-amber-500/20 text-amber-300'
            }`}>
              {pendingCases.length}
            </span>
          </button>
        </div>

        {/* Refresh & Search Tools */}
        <div className="flex items-center gap-3">
          <div className="relative min-w-[240px]">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by VIN..."
              className="form-input pl-8 py-1.5 text-xs rounded-xl"
              value={vinSearch}
              onChange={(e) => setVinSearch(e.target.value)}
            />
            {vinSearch && (
              <button
                onClick={() => setVinSearch('')}
                className="absolute right-2.5 top-2 text-[10px] text-slate-400 hover:text-white"
              >
                Clear
              </button>
            )}
          </div>

          {activeTab === 'myCases' && (
            <select
              className="form-input text-xs py-1.5 px-3 rounded-xl w-32"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="closed">Closed</option>
            </select>
          )}

          <button
            onClick={() => fetchCases()}
            className="btn btn-sm btn-secondary p-2 rounded-xl flex items-center gap-1.5 text-xs"
            title="Refresh case feed"
            disabled={loading}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Error alert */}
      {errorMsg && (
        <div className="alert-box alert-error">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Table Card */}
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/90 shadow-2xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400">
            <div className="spinner mb-3"></div>
            <span className="text-xs font-medium">Querying tenant-scoped database...</span>
          </div>
        ) : displayedCases.length === 0 ? (
          <div className="p-16 text-center text-slate-500">
            <Car className="w-12 h-12 mx-auto mb-3 text-slate-600 stroke-[1.5]" />
            <h3 className="text-base font-semibold text-slate-200">No cases found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              {activeTab === 'pendingClaims'
                ? 'No unclaimed repossession sightings are currently in the network pool. Use "Simulate Scan" in the header to transmit a new camera hit!'
                : 'Your agency has no active recovery orders matching the selected criteria.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-[11px] uppercase bg-slate-950/60 text-slate-400 border-b border-slate-800 font-bold tracking-wider">
                <tr>
                  <th className="py-3.5 px-5">Case Identifier</th>
                  <th className="py-3.5 px-5">Vehicle VIN</th>
                  <th className="py-3.5 px-5">Status</th>
                  {activeTab === 'pendingClaims' ? (
                    <th className="py-3.5 px-5">Originating Agency</th>
                  ) : (
                    <th className="py-3.5 px-5">Assigned Agent</th>
                  )}
                  <th className="py-3.5 px-5">Registered Date</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {displayedCases.map((c) => (
                  <tr
                    key={c.id}
                    className="hover:bg-slate-800/30 transition-colors group cursor-pointer"
                    onClick={() => {
                      if (c.status !== 'pending_claim') {
                        window.location.href = `/cases/${c.id}`;
                      }
                    }}
                  >
                    <td className="py-4 px-5 font-mono text-xs text-slate-400">
                      <span className="group-hover:text-indigo-400 transition-colors">
                        {c.id.slice(0, 8)}...
                      </span>
                    </td>

                    <td className="py-4 px-5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                          {c.vin}
                        </span>
                        <button
                          onClick={(e) => handleCopy(c.vin, e)}
                          className="p-1 rounded text-slate-500 hover:text-slate-300 transition"
                          title="Copy VIN"
                        >
                          {copiedVin === c.vin ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </td>

                    <td className="py-4 px-5">
                      <StatusBadge status={c.status} size="sm" />
                    </td>

                    {activeTab === 'pendingClaims' ? (
                      <td className="py-4 px-5 text-xs text-slate-300">
                        <span className="flex items-center gap-1.5">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" />
                          <span>{c.origin_tenant_name || 'Discovered by Camera Network'}</span>
                        </span>
                      </td>
                    ) : (
                      <td className="py-4 px-5 text-xs text-slate-300">
                        <span className="font-medium text-slate-200">
                          {c.assigned_user_name || 'Unassigned Agent'}
                        </span>
                      </td>
                    )}

                    <td className="py-4 px-5 text-xs text-slate-400 font-mono">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-4 px-5 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        {c.status === 'pending_claim' ? (
                          <button
                            onClick={() => setClaimingCase(c)}
                            className="btn btn-sm btn-claim shadow-md shadow-amber-600/20 flex items-center gap-1.5"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Claim Case</span>
                          </button>
                        ) : (
                          <Link
                            to={`/cases/${c.id}`}
                            className="btn btn-sm btn-outline flex items-center gap-1 text-xs"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>View Trail</span>
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Claim Modal */}
      <ClaimModal
        caseItem={claimingCase}
        isOpen={Boolean(claimingCase)}
        onClose={() => setClaimingCase(null)}
        onClaimSuccess={handleClaimSuccess}
      />
    </div>
  );
};
