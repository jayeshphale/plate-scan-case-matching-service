import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { casesApi } from '../api/cases';
import { Case, Scan } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { LocationTrail } from '../components/LocationTrail';
import { InteractiveMap } from '../components/InteractiveMap';
import { ClaimModal } from '../components/ClaimModal';
import {
  ArrowLeft,
  Calendar,
  Building2,
  User,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Fingerprint,
  Map,
  ListFilter,
  Copy,
  Check
} from 'lucide-react';

export const CaseDetails: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();

  const [caseItem, setCaseItem] = useState<Case | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // View mode: both or map focus
  const [viewMode, setViewMode] = useState<'split' | 'mapOnly' | 'trailOnly'>('split');

  // Claim modal state
  const [isClaimModalOpen, setIsClaimModalOpen] = useState(false);

  const fetchData = async () => {
    if (!caseId) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const [caseData, scansData] = await Promise.all([
        casesApi.getCase(caseId),
        casesApi.getCaseScans(caseId),
      ]);
      setCaseItem(caseData);
      setScans(scansData);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setErrorMsg('Access Denied: Tenant isolation strictly prohibits viewing active/closed cases owned by other recovery agencies.');
      } else if (err.response?.status === 404) {
        setErrorMsg('Case record not found.');
      } else {
        setErrorMsg(err.response?.data?.detail || 'Failed to load case details.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [caseId]);

  const handleCopyVin = () => {
    if (caseItem) {
      navigator.clipboard.writeText(caseItem.vin);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClaimSuccess = (updated: Case) => {
    setCaseItem(updated);
    fetchData();
  };

  if (loading) {
    return (
      <div className="p-20 flex flex-col items-center justify-center text-slate-400">
        <div className="spinner mb-4"></div>
        <span className="text-sm font-medium">Reconstructing vehicle sighting trail...</span>
      </div>
    );
  }

  if (errorMsg || !caseItem) {
    return (
      <div className="max-w-2xl mx-auto p-8 mt-12 bg-slate-900 border border-slate-800 rounded-2xl text-center shadow-2xl">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white mb-2">Access Protected</h3>
        <p className="text-sm text-slate-400 mb-6">{errorMsg || 'Unable to retrieve case details.'}</p>
        <Link to="/" className="btn btn-secondary inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Breadcrumb Bar */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-slate-900"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Operations Dashboard</span>
        </Link>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1 rounded-lg transition font-medium ${
                viewMode === 'split' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Split View
            </button>
            <button
              onClick={() => setViewMode('mapOnly')}
              className={`px-3 py-1 rounded-lg transition font-medium flex items-center gap-1 ${
                viewMode === 'mapOnly' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Map className="w-3.5 h-3.5" />
              <span>Map Only</span>
            </button>
            <button
              onClick={() => setViewMode('trailOnly')}
              className={`px-3 py-1 rounded-lg transition font-medium flex items-center gap-1 ${
                viewMode === 'trailOnly' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span>Timeline Only</span>
            </button>
          </div>

          <button
            onClick={fetchData}
            className="btn btn-sm btn-secondary flex items-center gap-1.5 text-xs rounded-xl"
            title="Refresh GPS telemetry"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Case Header Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
        <div className="flex flex-wrap items-start justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                CASE ID: {caseItem.id.slice(0, 13)}...
              </span>
              <StatusBadge status={caseItem.status} />
            </div>

            <div className="flex items-center gap-3">
              <h2 className="text-2xl sm:text-3xl font-bold font-mono text-white flex items-center gap-2">
                <Fingerprint className="w-7 h-7 text-indigo-400" />
                <span>{caseItem.vin}</span>
              </h2>

              <button
                onClick={handleCopyVin}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-white transition"
                title="Copy VIN"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {caseItem.status === 'pending_claim' && (
            <button
              onClick={() => setIsClaimModalOpen(true)}
              className="btn btn-claim py-2.5 px-5 shadow-xl shadow-amber-600/30 flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span className="font-bold">Claim This Opportunity</span>
            </button>
          )}
        </div>

        {/* Telemetry Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80">
            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mb-1">
              <Building2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Owning Agency</span>
            </span>
            <span className="text-sm font-semibold text-slate-100">
              {caseItem.tenant_name || 'Unassigned (Open Claim)'}
            </span>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80">
            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mb-1">
              <User className="w-3.5 h-3.5 text-emerald-400" />
              <span>Assigned Agent</span>
            </span>
            <span className="text-sm font-semibold text-slate-100">
              {caseItem.assigned_user_name || 'Unassigned'}
            </span>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80">
            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mb-1">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              <span>Discovery Camera Agency</span>
            </span>
            <span className="text-sm font-semibold text-slate-100">
              {caseItem.origin_tenant_name || 'Camera Webhook'}
            </span>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80">
            <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1.5 mb-1">
              <Calendar className="w-3.5 h-3.5 text-rose-400" />
              <span>Case Opened At</span>
            </span>
            <span className="text-sm font-mono text-slate-300">
              {new Date(caseItem.created_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Map Visualizer */}
      {(viewMode === 'split' || viewMode === 'mapOnly') && (
        <InteractiveMap scans={scans} vin={caseItem.vin} />
      )}

      {/* Chronological Timeline Trail */}
      {(viewMode === 'split' || viewMode === 'trailOnly') && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          <LocationTrail scans={scans} isLoading={loading} />
        </div>
      )}

      <ClaimModal
        caseItem={caseItem}
        isOpen={isClaimModalOpen}
        onClose={() => setIsClaimModalOpen(false)}
        onClaimSuccess={handleClaimSuccess}
      />
    </div>
  );
};
