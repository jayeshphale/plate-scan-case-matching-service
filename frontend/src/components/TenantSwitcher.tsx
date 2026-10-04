import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Building2, ChevronDown, Check, UserCheck, Shield } from 'lucide-react';

interface AccountOption {
  username: string;
  agencyLabel: string;
  agencyName: string;
  role: string;
  badgeColor: string;
}

const DEMO_ACCOUNTS: AccountOption[] = [
  {
    username: 'tenant_a_user',
    agencyLabel: 'Agency A (Staff)',
    agencyName: 'Recovery Agency A',
    role: 'staff',
    badgeColor: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
  },
  {
    username: 'tenant_a_admin',
    agencyLabel: 'Agency A (Admin)',
    agencyName: 'Recovery Agency A',
    role: 'admin',
    badgeColor: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
  },
  {
    username: 'tenant_b_user',
    agencyLabel: 'Agency B (Staff)',
    agencyName: 'Recovery Agency B',
    role: 'staff',
    badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  },
  {
    username: 'tenant_b_admin',
    agencyLabel: 'Agency B (Admin)',
    agencyName: 'Recovery Agency B',
    role: 'admin',
    badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  },
];

export const TenantSwitcher: React.FC = () => {
  const { user, login } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  const currentAccount = DEMO_ACCOUNTS.find((acc) => acc.username === user?.username) || DEMO_ACCOUNTS[0];

  const handleSwitch = async (account: AccountOption) => {
    if (account.username === user?.username) {
      setIsOpen(false);
      return;
    }
    setSwitching(true);
    try {
      await login(account.username, 'password123');
      setIsOpen(false);
    } catch (err) {
      console.error('Failed to switch tenant:', err);
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-850 border border-slate-700/80 hover:border-slate-600 text-xs transition shadow-sm"
        disabled={switching}
      >
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <Building2 className="w-4 h-4 text-indigo-400" />
        <div className="text-left">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block leading-none mb-0.5">
            Active Tenant
          </span>
          <span className="font-bold text-slate-100 block">
            {user?.tenant_name || currentAccount.agencyName}
          </span>
        </div>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 ml-1 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-2 z-40 animate-fade-in">
            <div className="px-3 py-2 border-b border-slate-800 text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              Switch Tenant Identity
            </div>
            <div className="space-y-1 mt-1">
              {DEMO_ACCOUNTS.map((acc) => {
                const isSelected = acc.username === user?.username;
                return (
                  <button
                    key={acc.username}
                    onClick={() => handleSwitch(acc)}
                    className={`w-full text-left p-2.5 rounded-xl text-xs flex items-center justify-between transition ${
                      isSelected
                        ? 'bg-indigo-600/15 border border-indigo-500/30 text-white'
                        : 'hover:bg-slate-800/80 text-slate-300'
                    }`}
                  >
                    <div>
                      <div className="font-semibold flex items-center gap-1.5">
                        <span>{acc.agencyLabel}</span>
                        {acc.role === 'admin' ? (
                          <Shield className="w-3 h-3 text-amber-400" />
                        ) : (
                          <UserCheck className="w-3 h-3 text-slate-400" />
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">{acc.username}</span>
                    </div>

                    {isSelected && <Check className="w-4 h-4 text-indigo-400" />}
                  </button>
                );
              })}
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800/80 px-2 text-[10px] text-slate-500 text-center">
              Demonstrates backend tenant isolation on the fly
            </div>
          </div>
        </>
      )}
    </div>
  );
};
