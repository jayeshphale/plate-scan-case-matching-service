import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { IngestScanModal } from '../components/IngestScanModal';

export const MainLayout: React.FC = () => {
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleScanCompleted = () => {
    // Increment trigger to notify active child pages to refetch
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar onOpenScanModal={() => setIsScanModalOpen(true)} />
      
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Outlet context={{ refreshTrigger }} />
      </main>

      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        Plate Scan & Case Matching Service — Multi-Tenant Architecture & Concurrency Defense
      </footer>

      <IngestScanModal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        onScanCompleted={handleScanCompleted}
      />
    </div>
  );
};
