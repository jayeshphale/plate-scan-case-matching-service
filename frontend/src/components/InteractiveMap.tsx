import React, { useState } from 'react';
import { Scan } from '../types';
import { MapPin, Navigation, ExternalLink, Crosshair, Layers, Eye } from 'lucide-react';

interface Props {
  scans: Scan[];
  vin: string;
}

export const InteractiveMap: React.FC<Props> = ({ scans, vin }) => {
  const [selectedScan, setSelectedScan] = useState<Scan | null>(scans[scans.length - 1] || null);
  const [showGrid, setShowGrid] = useState(true);

  if (scans.length === 0) {
    return (
      <div className="h-72 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex flex-col items-center justify-center text-slate-500">
        <Crosshair className="w-8 h-8 text-slate-600 mb-2 animate-spin-slow" />
        <p className="text-sm font-medium">Awaiting GPS telemetry data...</p>
      </div>
    );
  }

  // Calculate bounding box for coordinates
  const lats = scans.map((s) => s.latitude);
  const lngs = scans.map((s) => s.longitude);

  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  // Add padding margin to map viewBox
  const latDelta = Math.max(maxLat - minLat, 0.005);
  const lngDelta = Math.max(maxLng - minLng, 0.005);

  const padLat = latDelta * 0.25;
  const padLng = lngDelta * 0.25;

  const bMinLat = minLat - padLat;
  const bMaxLat = maxLat + padLat;
  const bMinLng = minLng - padLng;
  const bMaxLng = maxLng + padLng;

  // SVG dimensions
  const svgWidth = 800;
  const svgHeight = 420;

  // Project lat/lng to SVG (x, y) coordinates
  const project = (lat: number, lng: number) => {
    const x = ((lng - bMinLng) / (bMaxLng - bMinLng)) * (svgWidth - 120) + 60;
    // Invert Y because latitude increases northward while SVG Y increases downward
    const y = ((bMaxLat - lat) / (bMaxLat - bMinLat)) * (svgHeight - 100) + 50;
    return { x, y };
  };

  const points = scans.map((s) => ({
    ...project(s.latitude, s.longitude),
    scan: s,
  }));

  // Create SVG path string connecting sightings chronologically
  const pathD = points.reduce((acc, pt, idx) => {
    return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
  }, '');

  // Average center for Google Maps link
  const centerLat = (minLat + maxLat) / 2;
  const centerLng = (minLng + maxLng) / 2;

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
      {/* Top Map Header Controls */}
      <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between pointer-events-none">
        <div className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-700/60 text-xs shadow-lg">
          <Navigation className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          <span className="font-semibold text-slate-200">GPS Route Trail</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400 font-mono">{scans.length} sightings logged</span>
        </div>

        <div className="pointer-events-auto flex items-center gap-2">
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`p-2 rounded-xl border text-xs flex items-center gap-1.5 backdrop-blur-md transition ${
              showGrid
                ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-900/80 border-slate-700 text-slate-400'
            }`}
            title="Toggle Radar Grid"
          >
            <Layers className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Radar Grid</span>
          </button>

          <a
            href={`https://www.google.com/maps/dir/${scans.map((s) => `${s.latitude},${s.longitude}`).join('/')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 px-3 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white text-xs flex items-center gap-1.5 backdrop-blur-md transition"
          >
            <span>Google Maps</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </a>
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div className="w-full h-80 sm:h-96 relative cursor-crosshair overflow-hidden">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-full select-none"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Background Map Grid Pattern */}
            <pattern id="radarGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke="rgba(51, 65, 85, 0.25)"
                strokeWidth="0.8"
              />
            </pattern>
            {/* Secondary micro-grid */}
            <pattern id="microGrid" width="10" height="10" patternUnits="userSpaceOnUse">
              <path
                d="M 10 0 L 0 0 0 10"
                fill="none"
                stroke="rgba(51, 65, 85, 0.08)"
                strokeWidth="0.5"
              />
            </pattern>

            {/* Gradient for connecting route line */}
            <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.9" />
            </linearGradient>

            {/* Glow Filter */}
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Deep Navy/Black Background */}
          <rect width="100%" height="100%" fill="#030712" />

          {/* Radar Grids */}
          {showGrid && (
            <>
              <rect width="100%" height="100%" fill="url(#microGrid)" />
              <rect width="100%" height="100%" fill="url(#radarGrid)" />

              {/* Radar concentric target circles */}
              <circle
                cx={svgWidth / 2}
                cy={svgHeight / 2}
                r="120"
                fill="none"
                stroke="rgba(99, 102, 241, 0.08)"
                strokeDasharray="4 4"
              />
              <circle
                cx={svgWidth / 2}
                cy={svgHeight / 2}
                r="220"
                fill="none"
                stroke="rgba(99, 102, 241, 0.05)"
                strokeDasharray="4 4"
              />
            </>
          )}

          {/* Chronological Route Path Vector */}
          {points.length > 1 && (
            <>
              {/* Outer shadow trail */}
              <path
                d={pathD}
                fill="none"
                stroke="#4338ca"
                strokeWidth="6"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.3"
              />
              {/* Core animated dashed route */}
              <path
                d={pathD}
                fill="none"
                stroke="url(#routeGradient)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="6 4"
              />
            </>
          )}

          {/* Waypoint Markers */}
          {points.map((pt, idx) => {
            const isLatest = idx === points.length - 1;
            const isSelected = selectedScan?.id === pt.scan.id;

            return (
              <g
                key={pt.scan.id}
                transform={`translate(${pt.x}, ${pt.y})`}
                className="cursor-pointer transition-transform duration-200"
                onClick={() => setSelectedScan(pt.scan)}
              >
                {/* Pulsing ring for latest sighting */}
                {isLatest && (
                  <circle
                    r="18"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="1.5"
                    className="animate-ping opacity-75"
                  />
                )}

                {/* Selection halo */}
                {isSelected && (
                  <circle
                    r="15"
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="2"
                    strokeDasharray="3 3"
                    className="animate-spin-slow"
                  />
                )}

                {/* Waypoint circle pin */}
                <circle
                  r={isLatest ? 10 : 8}
                  fill={isLatest ? '#10b981' : isSelected ? '#6366f1' : '#1e293b'}
                  stroke={isLatest ? '#34d399' : isSelected ? '#a5b4fc' : '#475569'}
                  strokeWidth="2"
                  filter={isLatest ? 'url(#glow)' : undefined}
                />

                {/* Waypoint Sequence Number */}
                <text
                  textAnchor="middle"
                  dy="3.5"
                  fill="#ffffff"
                  fontSize={isLatest ? '10' : '9'}
                  fontWeight="bold"
                  className="pointer-events-none font-mono"
                >
                  {idx + 1}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Waypoint Telemetry Drawer */}
        {selectedScan && (
          <div className="absolute bottom-4 left-4 right-4 sm:right-auto sm:max-w-md z-20 p-4 rounded-xl bg-slate-900/95 backdrop-blur-md border border-slate-700/80 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-mono">
                  Sighting #{scans.findIndex((s) => s.id === selectedScan.id) + 1} of {scans.length}
                </span>
                {selectedScan.id === scans[scans.length - 1].id && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400">
                    Latest Fix
                  </span>
                )}
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {new Date(selectedScan.scanned_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Plate Number</span>
                <span className="font-mono font-bold text-slate-100">{selectedScan.plate}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Camera Unit</span>
                <span className="font-mono text-slate-300">{selectedScan.camera_id}</span>
              </div>
              <div className="col-span-2 pt-1 border-t border-slate-800 flex items-center justify-between">
                <div className="font-mono text-[11px] text-slate-400 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-rose-400" />
                  <span>{selectedScan.latitude.toFixed(5)}, {selectedScan.longitude.toFixed(5)}</span>
                </div>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${selectedScan.latitude},${selectedScan.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-400 hover:text-indigo-300 text-[11px] inline-flex items-center gap-1 font-medium"
                >
                  <span>Open Point</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
