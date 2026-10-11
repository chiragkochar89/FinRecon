import React from 'react';
import { Layers } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  description?: string;
  batchId?: string;
  mode?: string;
  statusBadge?: React.ReactNode;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  batchId = 'FINREC-20260922-001',
  mode = 'LOCAL_DEMO',
  statusBadge,
  actions
}) => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: '24px',
      flexWrap: 'wrap',
      gap: '16px',
      borderBottom: '1px solid var(--border-color)',
      paddingBottom: '16px'
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
          <h1 style={{
            margin: 0,
            fontSize: '1.5rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.3px'
          }}>
            {title}
          </h1>
          {statusBadge}
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {description && (
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              {description}
            </p>
          )}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: '#EDF2F7',
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            fontWeight: 600
          }}>
            <Layers size={12} color="#4A5568" />
            <span>BATCH: <strong>{batchId}</strong></span>
            <span style={{ color: '#CBD5E1' }}>|</span>
            <span>MODE: <strong>{mode}</strong></span>
          </div>
        </div>
      </div>

      {actions && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {actions}
        </div>
      )}
    </div>
  );
};
