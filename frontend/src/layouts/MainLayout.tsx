import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LoginPage } from '../pages/LoginPage';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { DashboardPage } from '../pages/DashboardPage';
import { BatchProcessingPage } from '../pages/BatchProcessingPage';
import { TransactionsPage } from '../pages/TransactionsPage';
import { ExceptionsPage } from '../pages/ExceptionsPage';
import { ReportsPage } from '../pages/ReportsPage';
import { AuditPage } from '../pages/AuditPage';
import { HealthPage } from '../pages/HealthPage';
import { getHealth } from '../services/api';
import { SystemHealth } from '../types';
import { Building2 } from 'lucide-react';

export const MainLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState<SystemHealth>({
    status: 'ONLINE',
    mode: 'LOCAL_DEMO',
    service: 'FinRecon System',
    version: '2.0.0'
  });

  useEffect(() => {
    if (isAuthenticated) {
      getHealth().then(setHealth).catch(console.error);
    }
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
        <div className="p-3 bg-blue-600 rounded-xl shadow-lg border border-blue-400/30 flex items-center justify-center mb-4">
          <Building2 className="w-8 h-8 text-white animate-pulse" />
        </div>
        <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-300 font-medium">Verifying Security Session...</p>
        <p className="text-xs text-slate-400 mt-1 font-mono">FinRecon Enterprise RBAC</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardPage />;
      case 'batch': return <BatchProcessingPage />;
      case 'transactions': return <TransactionsPage />;
      case 'exceptions': return <ExceptionsPage />;
      case 'reports': return <ReportsPage />;
      case 'audit': return <AuditPage />;
      case 'health': return <HealthPage health={health} />;
      default: return <DashboardPage />;
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--workspace-bg)', display: 'flex', flexDirection: 'column' }}>
      <Header mode={health.mode} />
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main style={{
          flex: 1,
          backgroundColor: 'var(--workspace-bg)',
          minHeight: 'calc(100vh - 61px)',
          overflowY: 'auto',
          overflowX: 'hidden'
        }}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;

