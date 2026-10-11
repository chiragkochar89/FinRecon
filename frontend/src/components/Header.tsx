import React from 'react';
import { ExecutionMode } from '../types';
import { Shield, User, Database, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface HeaderProps {
  mode: ExecutionMode;
  onUserChange?: (username: string, role: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ mode }) => {
  const isReal = mode === 'REAL_MAINFRAME';
  const { user, role, logout } = useAuth();


  return (
    <header style={{
      backgroundColor: 'var(--navy-900)',
      color: '#FFFFFF',
      padding: '12px 24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderBottom: '1px solid #1E3A5F',
      flexWrap: 'wrap',
      gap: '16px',
      boxShadow: '0 2px 4px rgba(10, 25, 45, 0.15)'
    }}>
      {/* Brand & Subtitle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          backgroundColor: 'var(--blue-600)',
          width: '36px',
          height: '36px',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 4px rgba(37, 99, 235, 0.3)'
        }}>
          <Shield size={20} color="#FFFFFF" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{
              margin: 0,
              fontSize: '1.25rem',
              fontWeight: 800,
              letterSpacing: '-0.2px',
              color: '#FFFFFF'
            }}>
              FinRecon
            </h1>
            <span style={{
              backgroundColor: '#1E3A5F',
              color: '#93C5FD',
              fontSize: '0.65rem',
              fontWeight: 800,
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              letterSpacing: '0.5px'
            }}>
              ENTERPRISE PLATFORM
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '0.75rem', color: '#94A3B8' }}>
            Financial Transaction Processing & Automated Reconciliation
          </p>
        </div>
      </div>

      {/* Right Controls: Identity Selector + Mode Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        {/* Authenticated Operator Profile & Role Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: '#0F1A2A',
          padding: '5px 12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid #1E3A5F'
        }}>
          <div style={{
            backgroundColor: '#1E293B',
            borderRadius: '50%',
            width: '26px',
            height: '26px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#93C5FD'
          }}>
            <User size={14} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.8rem', color: '#F8FAFC', fontWeight: 700 }}>
              {user?.full_name || user?.username || 'Authenticated User'}
            </span>
            <span style={{ fontSize: '0.65rem', color: '#94A3B8', fontFamily: 'var(--font-mono)' }}>
              @{user?.username || 'operator'}
            </span>
          </div>

          <span style={{
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.7rem',
            fontWeight: 800,
            backgroundColor: role === 'SUPERVISOR' ? '#78350F' : '#1E293B',
            color: role === 'SUPERVISOR' ? '#FCD34D' : '#93C5FD',
            border: role === 'SUPERVISOR' ? '1px solid #D97706' : '1px solid #3B82F6'
          }}>
            ROLE: {role}
          </span>

          <button
            onClick={() => logout()}
            title="Sign out of FinRecon"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: '#1E293B',
              color: '#F87171',
              border: '1px solid #991B1B',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 8px',
              fontSize: '0.7rem',
              fontWeight: 700,
              cursor: 'pointer',
              marginLeft: '4px',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#991B1B';
              e.currentTarget.style.color = '#FFFFFF';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#1E293B';
              e.currentTarget.style.color = '#F87171';
            }}
          >
            <LogOut size={12} />
            <span>Sign Out</span>
          </button>
        </div>


        {/* Mode Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: isReal ? '#064E3B' : '#1E293B',
          border: `1px solid ${isReal ? '#10B981' : '#F59E0B'}`,
          padding: '5px 12px',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.75rem',
          fontWeight: 700,
          color: isReal ? '#34D399' : '#FBBF24'
        }} title={isReal ? 'IBM z/OS Mainframe Connected' : 'Simulated Feeds & Persistent SQLite Storage'}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isReal ? '#34D399' : '#F59E0B',
            display: 'inline-block',
            boxShadow: `0 0 6px ${isReal ? '#10B981' : '#F59E0B'}`
          }} />
          <Database size={13} style={{ opacity: 0.9 }} />
          <span>MODE: {mode}</span>
        </div>
      </div>
    </header>
  );
};
