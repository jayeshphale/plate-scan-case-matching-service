import React, { useState } from 'react';
import { Case } from '../types';
import { casesApi } from '../api/cases';
import { AlertCircle, Check, X, ShieldAlert } from 'lucide-react';

interface Props {
  caseItem: Case | null;
  isOpen: boolean;
  onClose: () => void;
  onClaimSuccess: (updatedCase: Case) => void;
}

export const ClaimModal: React.FC<Props> = ({
  caseItem,
  isOpen,
  onClose,
  onClaimSuccess,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen || !caseItem) return null;

  const handleClaim = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const updated = await casesApi.claimCase(caseItem.id);
      onClaimSuccess(updated);
      onClose();
    } catch (err: any) {
      if (err.response?.status === 409) {
        setErrorMsg('Conflict: This case has already been claimed by another user or agency.');
      } else {
        setErrorMsg(err.response?.data?.detail || 'Failed to claim case. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <h3 className="modal-title">Confirm Case Claim</h3>
              <p className="modal-subtitle">Cross-tenant claim authorization</p>
            </div>
          </div>
          <button onClick={onClose} className="btn-close" disabled={isSubmitting}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="modal-body">
          {errorMsg && (
            <div className="alert-box alert-error mb-4">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="info-summary-box">
            <div className="summary-row">
              <span className="summary-label">Vehicle VIN:</span>
              <span className="summary-value font-mono">{caseItem.vin}</span>
            </div>
            <div className="summary-row">
              <span className="summary-label">Originating Agency:</span>
              <span className="summary-value">{caseItem.origin_tenant_name || 'Partner Truck Network'}</span>
            </div>
            <div className="summary-row">
              <span className="summary-label">Current Status:</span>
              <span className="summary-value text-amber-400 font-semibold">Pending Claim</span>
            </div>
          </div>

          <p className="modal-disclaimer">
            By claiming this case, it will immediately transition to <strong>Active</strong> status and be 
            exclusively assigned to your agency and account. Other agencies will no longer be able to claim or view this case.
          </p>
        </div>

        <div className="modal-footer">
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleClaim}
            className="btn btn-primary btn-claim"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <span className="spinner-sm"></span>
                <span>Claiming Case...</span>
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                <span>Confirm & Claim</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
