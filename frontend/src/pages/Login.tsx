import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield, Lock, User, ArrowRight, AlertCircle, Building2 } from 'lucide-react';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      await login(username.trim(), password);
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (userPreset: string) => {
    setUsername(userPreset);
    setPassword('password123');
    setErrorMsg(null);
    setLoading(true);

    try {
      await login(userPreset, 'password123');
      navigate('/');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Quick login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Branding header */}
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-indigo-600 items-center justify-center text-white mb-4 shadow-xl shadow-indigo-600/30">
            <Shield className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Plate Scan & Case Matching</h2>
          <p className="text-sm text-slate-400 mt-1">Multi-tenant LPR Vehicle Repossession Platform</p>
        </div>

        {/* Login form card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
          {errorMsg && (
            <div className="alert-box alert-error mb-4">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="form-label">Username</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  className="form-input pl-9"
                  placeholder="e.g. tenant_a_user"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="form-label">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="password"
                  className="form-input pl-9"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full py-2.5 mt-2 flex items-center justify-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-sm"></span>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Switcher */}
          <div className="mt-8 pt-6 border-t border-slate-800">
            <div className="flex items-center gap-2 mb-3">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Demo Accounts (Click to Login):
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('tenant_a_user')}
                className="btn btn-sm btn-outline text-left p-2.5 flex flex-col items-start border-slate-700 hover:border-indigo-500 hover:bg-slate-800/60"
                disabled={loading}
              >
                <span className="text-xs font-bold text-slate-200">Agency A (Staff)</span>
                <span className="text-[10px] text-slate-400 font-mono">tenant_a_user</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('tenant_b_user')}
                className="btn btn-sm btn-outline text-left p-2.5 flex flex-col items-start border-slate-700 hover:border-emerald-500 hover:bg-slate-800/60"
                disabled={loading}
              >
                <span className="text-xs font-bold text-slate-200">Agency B (Staff)</span>
                <span className="text-[10px] text-slate-400 font-mono">tenant_b_user</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('tenant_a_admin')}
                className="btn btn-sm btn-outline text-left p-2.5 flex flex-col items-start border-slate-700 hover:border-indigo-500 hover:bg-slate-800/60"
                disabled={loading}
              >
                <span className="text-xs font-bold text-slate-200">Agency A (Admin)</span>
                <span className="text-[10px] text-slate-400 font-mono">tenant_a_admin</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('tenant_b_admin')}
                className="btn btn-sm btn-outline text-left p-2.5 flex flex-col items-start border-slate-700 hover:border-emerald-500 hover:bg-slate-800/60"
                disabled={loading}
              >
                <span className="text-xs font-bold text-slate-200">Agency B (Admin)</span>
                <span className="text-[10px] text-slate-400 font-mono">tenant_b_admin</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-500 text-center mt-3">Demo password: password123</p>
          </div>
        </div>
      </div>
    </div>
  );
};
