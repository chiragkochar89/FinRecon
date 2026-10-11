import React from 'react';
import {
  LayoutDashboard,
  Layers,
  ArrowLeftRight,
  AlertTriangle,
  FileText,
  History,
  Activity,
  CheckCircle2
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'batch', label: 'Batch Processing', icon: <Layers size={18} /> },
    { id: 'transactions', label: 'Transactions', icon: <ArrowLeftRight size={18} /> },
    { id: 'exceptions', label: 'Exceptions', icon: <AlertTriangle size={18} /> },
    { id: 'reports', label: 'Reports', icon: <FileText size={18} /> },
    { id: 'audit', label: 'Audit Trail', icon: <History size={18} /> },
    { id: 'health', label: 'System Health', icon: <Activity size={18} /> }
  ];

  return (
    <aside style={{
      width: '240px',
      backgroundColor: 'var(--navy-900)',
      color: '#CBD5E1',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      minHeight: 'calc(100vh - 61px)',
      borderRight: '1px solid #1E3A5F',
      flexShrink: 0
    }}>
      <nav style={{ padding: '16px 0' }}>
        <div style={{
          padding: '0 20px 10px',
          fontSize: '0.65rem',
          fontWeight: 800,
          color: '#64748B',
          letterSpacing: '1px',
          textTransform: 'uppercase'
        }}>
          Operations Menu
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {tabs.map(tab => {
            const isActive = activeTab === tab.id;
            return (
              <li key={tab.id} style={{ marginBottom: '2px' }}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '10px 20px',
                    backgroundColor: isActive ? 'var(--navy-800)' : 'transparent',
                    color: isActive ? '#FFFFFF' : '#94A3B8',
                    border: 'none',
                    borderLeft: isActive ? '4px solid var(--blue-600)' : '4px solid transparent',
                    cursor: 'pointer',
                    fontWeight: isActive ? 700 : 500,
                    fontSize: '0.875rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = '#1A2C46';
                      e.currentTarget.style.color = '#F1F5F9';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = '#94A3B8';
                    }
                  }}
                >
                  <span style={{ color: isActive ? 'var(--blue-600)' : '#64748B' }}>
                    {tab.icon}
                  </span>
                  <span>{tab.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Sidebar Footer with Active Batch Info */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid #1E3A5F',
        backgroundColor: '#0F1A2A',
        fontSize: '0.75rem',
        color: '#64748B'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10B981', fontWeight: 700, marginBottom: '4px' }}>
          <CheckCircle2 size={12} />
          <span>BATCH VERIFIED</span>
        </div>
        <div style={{ color: '#E2E8F0', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
          FINREC-20260922-001
        </div>
        <div style={{ color: '#64748B', marginTop: '2px', fontSize: '0.7rem' }}>
          FinRecon v2.0.0 (Local Demo)
        </div>
      </div>
    </aside>
  );
};
