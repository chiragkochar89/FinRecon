import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

interface AlertBannerProps {
  type: 'success' | 'warning' | 'danger' | 'info';
  title?: string;
  message: React.ReactNode;
  onClose?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type,
  title,
  message,
  onClose
}) => {
  const getStyles = () => {
    switch (type) {
      case 'success':
        return {
          bg: 'var(--success-bg)',
          border: 'var(--success-border)',
          color: 'var(--success-text)',
          icon: <CheckCircle2 size={18} color="var(--success)" />
        };
      case 'warning':
        return {
          bg: 'var(--warning-bg)',
          border: 'var(--warning-border)',
          color: 'var(--warning-text)',
          icon: <AlertTriangle size={18} color="var(--warning)" />
        };
      case 'danger':
        return {
          bg: 'var(--danger-bg)',
          border: 'var(--danger-border)',
          color: 'var(--danger-text)',
          icon: <AlertCircle size={18} color="var(--danger)" />
        };
      case 'info':
      default:
        return {
          bg: 'var(--info-bg)',
          border: 'var(--info-border)',
          color: 'var(--info-text)',
          icon: <Info size={18} color="var(--blue-600)" />
        };
    }
  };

  const s = getStyles();

  return (
    <div style={{
      backgroundColor: s.bg,
      border: `1px solid ${s.border}`,
      borderRadius: 'var(--radius-md)',
      padding: '12px 16px',
      marginBottom: '16px',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: '12px',
      color: s.color,
      fontSize: '0.875rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
        <div style={{ marginTop: '2px', flexShrink: 0 }}>
          {s.icon}
        </div>
        <div>
          {title && <div style={{ fontWeight: 700, marginBottom: '2px' }}>{title}</div>}
          <div style={{ lineHeight: 1.4 }}>{message}</div>
        </div>
      </div>

      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
            color: s.color,
            opacity: 0.7
          }}
          aria-label="Dismiss alert"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};
