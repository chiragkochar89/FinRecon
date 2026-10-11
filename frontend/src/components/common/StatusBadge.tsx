import React from 'react';

export type BadgeType =
  | 'MATCHED'
  | 'AMOUNT-MISMATCH'
  | 'STATUS-MISMATCH'
  | 'MISSING-IN-BANK'
  | 'MISSING-IN-MERCHANT'
  | 'UNASSIGNED'
  | 'IN_REVIEW'
  | 'RESOLVED'
  | 'REJECTED'
  | 'CRITICAL'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'PASSED'
  | 'WARNING'
  | 'FAILED'
  | 'RECOVERED'
  | 'ONLINE'
  | 'LOCAL_DEMO';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const norm = (status || '').toUpperCase().trim();

  let badgeClass = 'fr-badge-neutral';
  let label = status;

  if (norm === 'MATCHED' || norm === 'RESOLVED' || norm === 'PASSED' || norm === 'ONLINE' || norm === 'COMPLETED') {
    badgeClass = 'fr-badge-success';
  } else if (norm === 'AMOUNT-MISMATCH' || norm === 'AMOUNT_MISMATCH' || norm === 'WARNING' || norm === 'IN_REVIEW' || norm === 'MEDIUM') {
    badgeClass = 'fr-badge-warning';
  } else if (norm === 'STATUS-MISMATCH' || norm === 'STATUS_MISMATCH' || norm === 'MISSING-IN-BANK' || norm === 'MISSING-IN-MERCHANT' || norm === 'CRITICAL' || norm === 'HIGH' || norm === 'FAILED' || norm === 'REJECTED') {
    badgeClass = 'fr-badge-danger';
  } else if (norm === 'UNASSIGNED' || norm === 'RECOVERED' || norm === 'LOCAL_DEMO') {
    badgeClass = 'fr-badge-info';
  }

  // Nicely format known keys
  if (norm === 'AMOUNT-MISMATCH') label = 'Amount Mismatch';
  else if (norm === 'STATUS-MISMATCH') label = 'Status Mismatch';
  else if (norm === 'MISSING-IN-BANK') label = 'Missing in Bank';
  else if (norm === 'MISSING-IN-MERCHANT') label = 'Missing in Merch';
  else if (norm === 'IN_REVIEW') label = 'In Review';
  else if (norm === 'UNASSIGNED') label = 'Unassigned';
  else if (norm === 'RESOLVED') label = 'Resolved';
  else if (norm === 'REJECTED') label = 'Rejected';

  return (
    <span
      className={`fr-badge ${badgeClass}`}
      style={{
        fontSize: size === 'sm' ? '10px' : '11px',
        padding: size === 'sm' ? '2px 6px' : '3px 8px'
      }}
    >
      {label}
    </span>
  );
};
