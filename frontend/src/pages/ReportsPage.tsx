import React, { useState, useEffect } from 'react';
import {
  exportExceptionsCsv,
  exportAuditCsv,
  exportReconciliationExcel,
  exportReconciliationPdf,
  getBatch
} from '../services/api';
import { BatchInfo } from '../types';
import { PageHeader } from '../components/common/PageHeader';
import { AlertBanner } from '../components/common/AlertBanner';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  Download,
  FileSpreadsheet,
  FileText,
  FileCode,
  ShieldAlert,
  CheckCircle2,
  Lock,
  Layers,
  Scale
} from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';

export const ReportsPage: React.FC = () => {
  const { user, role, isSupervisor } = useAuth();
  const [downloading, setDownloading] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [batchInfo, setBatchInfo] = useState<BatchInfo | null>(null);

  useEffect(() => {
    getBatch('FINREC-20260922-001').then(setBatchInfo).catch(console.error);
  }, []);

  const handleExport = async (type: string, fn: () => Promise<void>, label: string) => {
    setDownloading(type);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await fn();
      setSuccessMessage(`${label} downloaded successfully.`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Export failed. Server-side RBAC requires SUPERVISOR role permissions.');
    } finally {
      setDownloading(null);
    }
  };

  const finControls = batchInfo?.financial_controls;
  const summary = batchInfo?.summary;

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="Auditor-Ready Report & Export Center"
        description="Generate structured compliance audit reports, executive workbooks, and CSV logs from persistent database records."
        batchId="FINREC-20260922-001"
        mode="LOCAL_DEMO"
      />

      {/* RBAC NOTICE FOR STANDARD USERS */}
      {!isSupervisor && (
        <AlertBanner
          type="warning"
          title="RBAC ACCESS CONTROL NOTICE"
          message={
            <span>
              Report export operations require <strong>SUPERVISOR</strong> role permissions. Your current active account (<strong>{user?.username}</strong>) has role <strong>{role}</strong>. Server-side authorization will reject export requests with HTTP 403 Forbidden. Sign in with a SUPERVISOR account (e.g. <code>finrecon_supervisor</code>) to perform compliance exports.
            </span>
          }
        />
      )}


      {errorMessage && (
        <AlertBanner
          type="danger"
          title="EXPORT ERROR (HTTP 403 FORBIDDEN)"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}

      {successMessage && (
        <AlertBanner
          type="success"
          message={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      {/* LIVE BATCH SUMMARY PREVIEW CARD */}
      <div className="fr-card" style={{ padding: '20px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="var(--blue-600)" />
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Active Reconciliation Summary Preview
            </h3>
          </div>
          <StatusBadge status="WARNING" size="sm" />
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '14px',
          backgroundColor: 'var(--panel-subtle)',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          fontSize: '0.85rem'
        }}>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600 }}>BANK SOURCE TOTAL</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }} className="fr-money">
              ${(finControls?.bank_total_amount ?? 94136.00).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{finControls?.bank_record_count ?? 50} records</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600 }}>MERCHANT SOURCE TOTAL</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }} className="fr-money">
              ${(finControls?.merch_total_amount ?? 60817.50).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{finControls?.merch_record_count ?? 50} records</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600 }}>MATCHED AMOUNT</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--success)', marginTop: '2px' }} className="fr-money">
              ${(finControls?.matched_amount ?? 37515.00).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--success)' }}>{summary?.matched_count ?? 30} transactions (100% matched)</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600 }}>EXCEPTION EXPOSURE</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--danger)', marginTop: '2px' }} className="fr-money">
              ${(finControls?.total_exception_amount ?? 54913.50).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--danger)' }}>{summary?.total_exceptions ?? 30} cases requiring triage</div>
          </div>
        </div>
      </div>

      {/* 4 EXPORT CARDS GRID */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '20px'
      }}>
        {/* Card 1: Exceptions CSV */}
        <div className="fr-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{
                backgroundColor: 'var(--blue-50)',
                color: 'var(--blue-600)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 800
              }}>
                CSV FORMAT
              </div>
              <FileCode size={20} color="var(--blue-600)" />
            </div>

            <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Exceptions Dataset Export
            </h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Full tabular export of all 30 transaction discrepancies, reason codes, severities, triage states, and resolution notes.
            </p>
          </div>

          <button
            onClick={() => handleExport('csv_exc', exportExceptionsCsv, 'Exceptions CSV')}
            disabled={downloading !== null}
            className="fr-btn fr-btn-primary"
            style={{ marginTop: '24px', width: '100%' }}
          >
            <Download size={16} />
            <span>{downloading === 'csv_exc' ? 'Generating CSV...' : 'Download Exceptions CSV'}</span>
          </button>
        </div>

        {/* Card 2: Audit CSV */}
        <div className="fr-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{
                backgroundColor: '#F1F5F9',
                color: '#475569',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 800
              }}>
                CSV FORMAT
              </div>
              <FileText size={20} color="#475569" />
            </div>

            <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Operational Audit Trail Export
            </h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Immutable append-only audit event log including chronological timestamps, actors, roles, status transitions, and notes.
            </p>
          </div>

          <button
            onClick={() => handleExport('csv_audit', exportAuditCsv, 'Audit Trail CSV')}
            disabled={downloading !== null}
            className="fr-btn fr-btn-secondary"
            style={{ marginTop: '24px', width: '100%' }}
          >
            <Download size={16} />
            <span>{downloading === 'csv_audit' ? 'Generating CSV...' : 'Download Audit Trail CSV'}</span>
          </button>
        </div>

        {/* Card 3: Excel Workbook */}
        <div className="fr-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{
                backgroundColor: 'var(--success-bg)',
                color: 'var(--success-text)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 800
              }}>
                EXCEL WORKBOOK (.XLSX)
              </div>
              <FileSpreadsheet size={20} color="var(--success)" />
            </div>

            <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Executive Excel Workbook
            </h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Structured 4-sheet multi-tab workbook with Executive Summary, Exceptions, Audit Trail, and Control Totals.
            </p>
          </div>

          <button
            onClick={() => handleExport('xlsx', exportReconciliationExcel, 'Excel Workbook')}
            disabled={downloading !== null}
            className="fr-btn"
            style={{ marginTop: '24px', width: '100%', backgroundColor: 'var(--success)', color: '#FFFFFF' }}
          >
            <Download size={16} />
            <span>{downloading === 'xlsx' ? 'Building Excel...' : 'Download Excel (.xlsx)'}</span>
          </button>
        </div>

        {/* Card 4: Management PDF */}
        <div className="fr-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{
                backgroundColor: 'var(--danger-bg)',
                color: 'var(--danger-text)',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 800
              }}>
                PDF REPORT (.PDF)
              </div>
              <FileText size={20} color="var(--danger)" />
            </div>

            <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Auditor Management PDF Report
            </h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Formal PDF compliance report with executive summary, category breakdown, conservation checks, and governance sign-off.
            </p>
          </div>

          <button
            onClick={() => handleExport('pdf', exportReconciliationPdf, 'PDF Report')}
            disabled={downloading !== null}
            className="fr-btn fr-btn-danger"
            style={{ marginTop: '24px', width: '100%' }}
          >
            <Download size={16} />
            <span>{downloading === 'pdf' ? 'Compiling PDF...' : 'Download PDF Report'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
