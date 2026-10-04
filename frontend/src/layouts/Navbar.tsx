import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { TenantSwitcher } from '../components/TenantSwitcher';
import { Shield, LogOut, Camera, User as UserIcon, Code2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

interface Props {
  onOpenScanModal: () => void;
}

export const Navbar: React.FC<Props> = ({ onOpenScanModal }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar-container">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Logo and Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-600/30 group-hover:scale-105 transition">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm sm:text-base font-bold text-slate-100 leading-tight">
                Plate Scan & Match
              </h1>
              <span className="hidden md:inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                v1.0 Live
              </span>
            </div>
            <span className="text-[11px] text-slate-400 font-medium">
              Multi-Tenant LPR Repo Service
            </span>
          </div>
        </Link>

        {user && (
          <div className="flex items-center gap-3">
            {/* Quick Webhook Ingestion Trigger */}
            <button
              onClick={onOpenScanModal}
              className="btn btn-sm btn-primary flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
              title="Simulate inbound camera scan webhook"
            >
              <Camera className="w-4 h-4" />
              <span className="hidden sm:inline">Simulate Scan</span>
            </button>

            {/* Quick Link to Swagger Docs */}
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden lg:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-xs text-slate-300 hover:text-white transition shadow-sm"
              title="Open OpenAPI Swagger UI"
            >
              <Code2 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Swagger API</span>
            </a>

            {/* One-Click Tenant Switcher */}
            <TenantSwitcher />

            {/* User Profile */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
              <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
                <UserIcon className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <div>
                <span className="font-semibold text-slate-200 block text-xs">{user.username}</span>
                <span className="text-[10px] text-slate-500 font-mono uppercase">{user.role}</span>
              </div>
            </div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="btn-icon text-slate-400 hover:text-rose-400 p-2 rounded-xl hover:bg-slate-900 border border-transparent hover:border-slate-800 transition"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
