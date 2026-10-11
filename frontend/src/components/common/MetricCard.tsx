import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon,
  badge,
  variant = 'default'
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'success':
        return {
          borderTop: '3px solid var(--success)',
          valueColor: '#065F46'
        };
      case 'warning':
        return {
          borderTop: '3px solid var(--warning)',
          valueColor: '#92400E'
        };
      case 'danger':
        return {
          borderTop: '3px solid var(--danger)',
          valueColor: '#991B1B'
        };
      case 'info':
        return {
          borderTop: '3px solid var(--blue-600)',
          valueColor: '#1E40AF'
        };
      default:
        return {
          borderTop: '3px solid #CBD5E1',
          valueColor: 'var(--text-primary)'
        };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <div
      className="fr-metric-card"
      style={{
        borderTop: vStyles.borderTop,
        position: 'relative'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <span style={{
          fontSize: '0.75rem',
          fontWeight: 700,
          color: 'var(--text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          {label}
        </span>
        {icon && (
          <div style={{ color: 'var(--text-muted)' }}>
            {icon}
          </div>
        )}
      </div>

      <div style={{
        fontSize: '1.65rem',
        fontWeight: 800,
        color: vStyles.valueColor,
        letterSpacing: '-0.5px',
        lineHeight: 1.2
      }}>
        {value}
      </div>

      {(subtext || badge) && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '10px',
          gap: '8px',
          fontSize: '0.75rem',
          color: 'var(--text-secondary)'
        }}>
          {subtext && <span>{subtext}</span>}
          {badge}
        </div>
      )}
    </div>
  );
};
