import React from 'react';
import { Scan } from '../types';
import { MapPin, Calendar, Camera, ExternalLink, Image as ImageIcon } from 'lucide-react';

interface Props {
  scans: Scan[];
  isLoading: boolean;
}

export const LocationTrail: React.FC<Props> = ({ scans, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <div className="spinner mb-3"></div>
        <span>Retrieving location trail...</span>
      </div>
    );
  }

  if (scans.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800">
        <MapPin className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p>No historical scans found for this VIN yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Chronological Sightings ({scans.length})
        </h4>
        <span className="text-xs text-slate-500">Ordered by timestamp (Oldest → Latest)</span>
      </div>

      <div className="relative border-l-2 border-indigo-500/30 ml-4 pl-6 space-y-6">
        {scans.map((scan, index) => {
          const formattedDate = new Date(scan.scanned_at).toLocaleString();
          const isLatest = index === scans.length - 1;

          return (
            <div key={scan.id} className="relative group">
              {/* Timeline pin point */}
              <div
                className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 transition-all ${
                  isLatest
                    ? 'bg-emerald-500 border-emerald-300 ring-4 ring-emerald-500/20'
                    : 'bg-slate-800 border-indigo-400'
                }`}
              />

              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/70 hover:border-slate-700 transition">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                      Sighting #{index + 1}
                    </span>
                    {isLatest && (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 animate-pulse">
                        Latest Sighting
                      </span>
                    )}
                    <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                      <Calendar className="w-3.5 h-3.5" />
                      {formattedDate}
                    </span>
                  </div>

                  <div className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 flex items-center gap-1">
                    <Camera className="w-3 h-3 text-slate-400" />
                    <span>{scan.camera_id}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                  <div>
                    <span className="text-xs text-slate-500 block">License Plate</span>
                    <span className="font-mono font-bold text-slate-200">{scan.plate}</span>
                  </div>

                  <div>
                    <span className="text-xs text-slate-500 block">Coordinates (Lat, Lng)</span>
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${scan.latitude},${scan.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-xs text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1 mt-0.5"
                    >
                      <MapPin className="w-3.5 h-3.5 text-rose-400" />
                      <span>{scan.latitude.toFixed(4)}, {scan.longitude.toFixed(4)}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  {scan.image_url && (
                    <div>
                      <span className="text-xs text-slate-500 block mb-1">Capture Image</span>
                      <a
                        href={scan.image_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-xs text-slate-300 hover:text-white group/img"
                      >
                        <img
                          src={scan.image_url}
                          alt="Plate Scan"
                          className="w-12 h-8 object-cover rounded border border-slate-700 group-hover/img:border-indigo-400 transition"
                        />
                        <span className="underline">View Full Photo</span>
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
