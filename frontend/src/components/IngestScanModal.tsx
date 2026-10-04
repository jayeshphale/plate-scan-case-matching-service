import React, { useState } from 'react';
import { scansApi } from '../api/scans';
import { ScanIngestResponse } from '../types';
import { Camera, Send, X, CheckCircle, AlertTriangle, RefreshCw, Zap, Terminal, Copy } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onScanCompleted: () => void;
}

export const IngestScanModal: React.FC<Props> = ({ isOpen, onClose, onScanCompleted }) => {
  const [cameraId, setCameraId] = useState('cam_1001');
  const [plate, setPlate] = useState('7XYZ123');
  const [vin, setVin] = useState('1FTFW1E51NFA12345');
  const [latitude, setLatitude] = useState('33.7490');
  const [longitude, setLongitude] = useState('-84.3880');
  const [imageUrl, setImageUrl] = useState('https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400');
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<ScanIngestResponse | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const loadPreset = (preset: 'flowA' | 'flowB' | 'ineligible') => {
    setErrorMsg(null);
    setResult(null);
    if (preset === 'flowA') {
      setCameraId('cam_1001');
      setPlate('7XYZ123');
      setVin('1FTFW1E51NFA12345');
      setLatitude('33.7490');
      setLongitude('-84.3880');
      setImageUrl('https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400');
    } else if (preset === 'flowB') {
      setCameraId('cam_2050');
      setPlate('2MNO456');
      setVin('5NPE34AF9KH123456');
      setLatitude('34.0522');
      setLongitude('-118.2437');
      setImageUrl('https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400');
    } else {
      setCameraId('cam_1001');
      setPlate('NOTREPO1');
      setVin('INELIGIBLE9999999');
      setLatitude('33.7505');
      setLongitude('-84.3890');
      setImageUrl('https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400');
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    setResult(null);

    const startTime = performance.now();
    try {
      const response = await scansApi.ingestScan({
        camera_id: cameraId.trim(),
        plate: plate.trim(),
        vin: vin.trim(),
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        scanned_at: new Date().toISOString(),
        image_url: imageUrl.trim() || undefined,
      });

      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);
      setResult(response);
      onScanCompleted();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Scan ingestion failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (result) {
      navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card modal-large max-h-[90vh] overflow-y-auto">
        <div className="modal-header sticky top-0 bg-slate-900/95 backdrop-blur-md z-10 border-b border-slate-800">
          <div className="modal-title-group">
            <div className="modal-icon-badge bg-indigo-500/10 text-indigo-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="modal-title">Truck Camera Webhook Simulator</h3>
              <p className="modal-subtitle">Triggers POST /api/v1/scans directly against backend pipeline</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-close" disabled={isLoading}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="modal-body space-y-4">
          {/* Quick Scenario Preset Selectors */}
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Assignment Scenarios (Click to Load):
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => loadPreset('flowA')}
                className="btn btn-sm btn-outline text-left p-2 flex flex-col items-start border-slate-700 hover:border-indigo-500 hover:bg-indigo-500/10"
              >
                <span className="font-bold text-slate-200">Scenario 1 (Flow A)</span>
                <span className="text-[10px] text-slate-400 font-mono">cam_1001 • Active Case</span>
              </button>

              <button
                type="button"
                onClick={() => loadPreset('flowB')}
                className="btn btn-sm btn-outline text-left p-2 flex flex-col items-start border-amber-500/40 hover:border-amber-400 hover:bg-amber-500/10"
              >
                <span className="font-bold text-amber-300">Scenario 2 (Flow B)</span>
                <span className="text-[10px] text-slate-400 font-mono">cam_2050 • Eligible VIN</span>
              </button>

              <button
                type="button"
                onClick={() => loadPreset('ineligible')}
                className="btn btn-sm btn-outline text-left p-2 flex flex-col items-start border-slate-700 hover:border-slate-500"
              >
                <span className="font-bold text-slate-300">Ineligible Vehicle</span>
                <span className="text-[10px] text-slate-400 font-mono">Retains scan history</span>
              </button>
            </div>
          </div>

          {errorMsg && (
            <div className="alert-box alert-error">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSimulate} className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div className="form-group">
              <label className="form-label">Camera Identifier</label>
              <input
                type="text"
                className="form-input font-mono"
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                placeholder="cam_1001, cam_2050"
                required
              />
              <span className="text-[10px] text-slate-500 mt-1">
                Resolved to Tenant in DB (cam_1001 = Agency A, cam_2050 = Agency B)
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">License Plate</label>
              <input
                type="text"
                className="form-input font-mono uppercase"
                value={plate}
                onChange={(e) => setPlate(e.target.value)}
                required
              />
            </div>

            <div className="form-group col-span-1 sm:col-span-2">
              <label className="form-label">Vehicle Identification Number (VIN)</label>
              <input
                type="text"
                className="form-input font-mono uppercase font-bold text-indigo-300"
                value={vin}
                onChange={(e) => setVin(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Latitude</label>
              <input
                type="number"
                step="any"
                className="form-input font-mono"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Longitude</label>
              <input
                type="number"
                step="any"
                className="form-input font-mono"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                required
              />
            </div>

            <div className="form-group col-span-1 sm:col-span-2">
              <label className="form-label">Capture Photo URL</label>
              <input
                type="url"
                className="form-input text-xs font-mono"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
              />
            </div>

            <div className="col-span-1 sm:col-span-2 flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary"
                disabled={isLoading}
              >
                Close
              </button>
              <button
                type="submit"
                className="btn btn-primary flex items-center gap-2"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Processing Ingest...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Fire Camera Webhook</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Real-time Response Inspector */}
          {result && (
            <div className="result-container p-4 rounded-xl border border-slate-700 bg-slate-950 font-mono text-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2 font-bold text-emerald-400">
                  <CheckCircle className="w-4 h-4" />
                  <span>HTTP 201 Created</span>
                  {latencyMs !== null && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                      {latencyMs}ms
                    </span>
                  )}
                </div>

                <button
                  onClick={handleCopyJson}
                  className="btn btn-sm btn-outline text-slate-400 hover:text-white flex items-center gap-1 text-[10px]"
                >
                  <Copy className="w-3 h-3" />
                  <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                <div>
                  <span className="text-slate-500">Flow Route:</span>{' '}
                  <span className={result.matched_existing_case ? 'text-emerald-400 font-bold' : result.created_new_case ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                    {result.matched_existing_case
                      ? 'Flow A (Active Case Trail)'
                      : result.created_new_case
                      ? 'Flow B (New Pending Claim)'
                      : 'Flow B (Ineligible / Stored)'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Resolved Tenant:</span>{' '}
                  <span className="font-mono text-slate-200">{result.tenant_id.slice(0, 8)}...</span>
                </div>
                {result.case_id && (
                  <div className="col-span-2">
                    <span className="text-slate-500">Target Case ID:</span>{' '}
                    <span className="text-indigo-300 font-bold">{result.case_id}</span>
                  </div>
                )}
              </div>

              <pre className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[10px] overflow-x-auto text-emerald-300">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
