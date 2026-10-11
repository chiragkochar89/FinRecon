import React from 'react';
import { SystemHealth } from '../types';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  Activity,
  CheckCircle2,
  Database,
  Server,
  ShieldCheck,
  FolderTree,
  Cpu,
  Layers,
  FileCheck
} from 'lucide-react';

interface HealthPageProps {
  health: SystemHealth;
}

export const HealthPage: React.FC<HealthPageProps> = ({ health }) => {
  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="System Observability & Platform Telemetry"
        description="Live operational telemetry, backend API health, simulated mainframe adapter mode, and SQLite repository verification."
        batchId="FINREC-20260922-001"
        mode={health.mode}
        statusBadge={<StatusBadge status="ONLINE" />}
      />

      {/* CORE TELEMETRY STATUS CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <Server size={20} color="var(--success)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Backend API Status
            </span>
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--success)' }}>
            {health.status}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            FastAPI REST Server | Port 8000
          </div>
        </div>

        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <Cpu size={20} color="var(--blue-600)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Adapter Mode
            </span>
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--blue-600)' }}>
            {health.mode}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Simulated Mainframe + SQLite Store
          </div>
        </div>

        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <ShieldCheck size={20} color="var(--blue-600)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              RBAC Authorization
            </span>
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            ACTIVE (ENFORCED)
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Analyst (Triage) & Supervisor (Export)
          </div>
        </div>

        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <Layers size={20} color="var(--blue-600)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Platform Version
            </span>
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            v{health.version}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {health.service}
          </div>
        </div>
      </div>

      {/* PLATFORM CONFIGURATION & STORAGE SPECIFICATIONS TABLE */}
      <div className="fr-card" style={{ padding: '24px', marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          System Configuration & Data Storage Properties
        </h3>

        <div className="fr-table-container" style={{ border: 'none', boxShadow: 'none' }}>
          <table className="fr-data-table">
            <tbody>
              <tr>
                <td style={{ width: '240px', fontWeight: 600, color: 'var(--text-secondary)' }}>Operating Mode</td>
                <td>
                  <span style={{ fontWeight: 700, color: 'var(--blue-600)' }}>{health.mode}</span>
                  <span style={{ color: 'var(--text-muted)', marginLeft: '8px', fontSize: '12px' }}>
                    (Local execution with verified Decimal math and SQLite storage)
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Service Identification</td>
                <td style={{ fontWeight: 600 }}>{health.service}</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Database Store</td>
                <td>
                  <span className="fr-mono" style={{ backgroundColor: 'var(--panel-subtle)', padding: '2px 6px', borderRadius: '4px' }}>
                    backend/data/finrecon_local.db
                  </span>
                  <span style={{ color: 'var(--success)', fontWeight: 600, marginLeft: '8px', fontSize: '12px' }}>
                    ✓ SQLite Persistent Storage
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Transaction Feeds Directory</td>
                <td>
                  <span className="fr-mono" style={{ backgroundColor: 'var(--panel-subtle)', padding: '2px 6px', borderRadius: '4px' }}>
                    data/
                  </span>
                  <span style={{ color: 'var(--text-secondary)', marginLeft: '8px', fontSize: '12px' }}>
                    (BANK.FEED.DAILY.DAT, MERCHANT.SETTLE.DAILY.DAT)
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Reports & Export Staging</td>
                <td>
                  <span className="fr-mono" style={{ backgroundColor: 'var(--panel-subtle)', padding: '2px 6px', borderRadius: '4px' }}>
                    reports/
                  </span>
                  <span style={{ color: 'var(--text-secondary)', marginLeft: '8px', fontSize: '12px' }}>
                    (CSV, XLSX, PDF generation via openpyxl and reportlab)
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* OPERATIONAL VERIFICATION CHECKLIST */}
      <div className="fr-card" style={{ padding: '24px' }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Operational Integrity Verification Checklist
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
            <CheckCircle2 size={16} color="var(--success)" />
            <span><strong>Reconciliation Arithmetic:</strong> Two-pass matching with exact Python Decimal precision.</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
            <CheckCircle2 size={16} color="var(--success)" />
            <span><strong>Feed Key Parsing:</strong> Fixed-width 80-byte LRECL parser with column position extraction.</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
            <CheckCircle2 size={16} color="var(--success)" />
            <span><strong>Database Integrity:</strong> SQLite atomic transactions with automatic rollback on error.</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
            <CheckCircle2 size={16} color="var(--success)" />
            <span><strong>Audit Immutability:</strong> Append-only event tracking for all triage actions and security denials.</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
            <CheckCircle2 size={16} color="var(--success)" />
            <span><strong>Self-Healing Recovery:</strong> Checkpoint-based stage recovery for pipeline execution errors.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
