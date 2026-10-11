import React, { useState, useEffect } from 'react';
import {
  validateFiles,
  executeBatch,
  resetBatchPipeline,
  getBatchControls,
  simulateControlFailure,
  recoverBatch,
  getBatchRecoveryEvents
} from '../services/api';
import { FileValidationResult, BatchInfo, ControlCheckpointModel, RecoveryEventModel } from '../types';
import { PageHeader } from '../components/common/PageHeader';
import { AlertBanner } from '../components/common/AlertBanner';
import {
  UploadCloud,
  FileCheck,
  Play,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Clock,
  Layers,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Ban
} from 'lucide-react';
import './BatchProcessingPage.css';

interface ParsedExceptionAlert {
  header: string;
  items: { code: string; count: string }[];
  rawRemainder?: string;
}

const parseExceptionReason = (reason?: string | null): ParsedExceptionAlert | null => {
  if (!reason) return null;

  const rcnRegex = /(RCN-[A-Z0-9]+)\s*(?:\((\d+)\)|:\s*(\d+))/gi;
  const items: { code: string; count: string }[] = [];
  let match: RegExpExecArray | null;
  let lastIndex = 0;
  let firstMatchIndex = -1;

  while ((match = rcnRegex.exec(reason)) !== null) {
    if (firstMatchIndex === -1) {
      firstMatchIndex = match.index;
    }
    items.push({
      code: match[1].toUpperCase(),
      count: match[2] || match[3] || '1',
    });
    lastIndex = rcnRegex.lastIndex;
  }

  if (items.length > 0) {
    let header = 'Exceptions Detected';
    if (firstMatchIndex > 0) {
      const prefix = reason.substring(0, firstMatchIndex).replace(/[:,\s]+$/, '').trim();
      if (prefix) {
        header = prefix;
      }
    }
    const remainder = reason.substring(lastIndex).replace(/^[:,\s]+/, '').trim();
    return {
      header,
      items,
      rawRemainder: remainder || undefined,
    };
  }

  return {
    header: 'Alert',
    items: [],
    rawRemainder: reason,
  };
};

const getStatusClass = (status: string): string => {
  switch (status) {
    case 'PASSED':
      return 'passed';
    case 'WARNING':
      return 'warning';
    case 'FAILED_CONTROL':
      return 'failed';
    case 'RECOVERED':
      return 'recovered';
    case 'HALTED':
    case 'STOPPED':
      return 'halted';
    case 'PENDING':
    default:
      return 'pending';
  }
};

export const BatchProcessingPage: React.FC = () => {
  const [batchId] = useState<string>('FINREC-20260922-001');
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<FileValidationResult | null>(null);
  const [processing, setProcessing] = useState(false);
  const [batchResult, setBatchResult] = useState<BatchInfo | null>(null);
  const [checkpoints, setCheckpoints] = useState<ControlCheckpointModel[]>([]);
  const [recoveryEvents, setRecoveryEvents] = useState<RecoveryEventModel[]>([]);
  const [recovering, setRecovering] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const currentUserRole = localStorage.getItem('finrecon_role') || 'USER';
  const isSupervisor = currentUserRole.toUpperCase() === 'SUPERVISOR' || currentUserRole.toUpperCase() === 'ADMIN';

  const loadControls = async (bId: string = batchId) => {
    try {
      const chks = await getBatchControls(bId);
      setCheckpoints(chks);
      const evts = await getBatchRecoveryEvents(bId);
      setRecoveryEvents(evts);
    } catch (err) {
      console.error('Error loading controls:', err);
    }
  };

  useEffect(() => {
    loadControls();
  }, [batchId]);

  const handleValidate = async () => {
    setValidating(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const res = await validateFiles();
      setValidationResult(res);
      setSuccessMessage('Pre-flight dataset validation completed successfully. Feeds meet LRECL/RECFM format requirements.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Validation failed.');
    } finally {
      setValidating(false);
    }
  };

  const handleStartRecon = async () => {
    setProcessing(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const res = await executeBatch(batchId);
      setBatchResult(res);
      setSuccessMessage('Reconciliation batch executed successfully. Stage controls and balance equations verified.');
      await loadControls(batchId);
    } catch (err: any) {
      setErrorMessage(err.message || 'Reconciliation execution failed.');
    } finally {
      setProcessing(false);
    }
  };

  const handleResetPipeline = async () => {
    setResetting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await resetBatchPipeline(batchId);
      setBatchResult(null);
      setValidationResult(null);
      await loadControls(batchId);
      setSuccessMessage('Pipeline reset to initial PENDING state. All stages unexecuted.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Pipeline reset failed.');
    } finally {
      setResetting(false);
    }
  };

  const handleSimulateFailure = async () => {
    setSimulating(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await simulateControlFailure(batchId, 'DFSORT_DEDUP', 'AMOUNT_CONTROL_MISMATCH');
      await loadControls(batchId);
      setSuccessMessage('Control failure simulated successfully on stage DFSORT_DEDUP (RC=12). Downstream pipeline halted safely.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failure simulation failed.');
    } finally {
      setSimulating(false);
    }
  };

  const handleTriggerRecovery = async () => {
    setRecovering(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await recoverBatch(batchId);
      await loadControls(batchId);
      setSuccessMessage('Self-healing batch recovery completed successfully. Pipeline checkpoint restored and verified.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Self-healing recovery failed.');
    } finally {
      setRecovering(false);
    }
  };

  const getStepStatus = (stageName: string) => {
    const chk = checkpoints.find(c => c.stage_name === stageName);
    if (chk) {
      if (chk.control_status === 'FAILED_CONTROL') {
        return { text: `FAILED (RC=${chk.return_code})`, color: 'var(--danger)', bg: 'var(--danger-bg)', statusType: 'failed' };
      }
      if (chk.control_status === 'RECOVERED') {
        return { text: 'RECOVERED (RC=00)', color: 'var(--info-text)', bg: 'var(--info-bg)', statusType: 'recovered' };
      }
      if (chk.control_status === 'WARNING') {
        return { text: 'WARNING (RC=04)', color: 'var(--warning-text)', bg: 'var(--warning-bg)', statusType: 'warning' };
      }
      if (chk.control_status === 'PASSED') {
        const rcStr = chk.return_code === 4 ? 'RC=04' : 'RC=00';
        return { text: `COMPLETED (${rcStr})`, color: 'var(--success-text)', bg: 'var(--success-bg)', statusType: 'passed' };
      }
      if (chk.control_status === 'HALTED' || chk.control_status === 'STOPPED') {
        return { text: 'HALTED (DOWNSTREAM)', color: 'var(--warning-text)', bg: 'var(--warning-bg)', statusType: 'halted' };
      }
      if (chk.control_status === 'PROCESSING') {
        return { text: 'PROCESSING...', color: 'var(--blue-600)', bg: 'var(--blue-50)', statusType: 'processing' };
      }
      if (chk.control_status === 'PENDING') {
        return { text: 'PENDING', color: 'var(--text-muted)', bg: '#F1F5F9', statusType: 'pending' };
      }
    }
    return { text: 'PENDING', color: 'var(--text-muted)', bg: '#F1F5F9', statusType: 'pending' };
  };

  const steps = [
    { num: '01', name: 'Input Validation & Format Verification', stage: 'INPUT_VALIDATION' },
    { num: '02', name: 'Bank Feed DFSORT Deduplication (Cols 13–20)', stage: 'DFSORT_DEDUP' },
    { num: '03', name: 'Merchant Feed DFSORT Ascending Sort (Cols 21–28)', stage: 'MERCHANT_SORT' },
    { num: '04', name: 'COBOL Reconciliation Engine Execution (FINREC01)', stage: 'COBOL_RECONCILIATION' },
    { num: '05', name: 'REXX Audit Processor Execution (FINREXX - Cols 25–32)', stage: 'REXX_PROCESSING' },
    { num: '06', name: 'JCL Descending Sort Record Count Validation', stage: 'JCL_CONTROL' },
    { num: '07', name: 'COBOL Report Summary Generator Execution (FINRPT01)', stage: 'REPORT_GENERATION' },
    { num: '08', name: 'Batch Final Disposition & Cataloging', stage: 'FINAL_DISPOSITION' }
  ];

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="Batch Processing & Pipeline Orchestration"
        description="Pre-flight feed validation, simulated z/OS batch execution stream, stage checkpoints, and self-healing recovery."
        batchId={batchId}
        mode="LOCAL_DEMO"
      />

      {/* BANNERS */}
      {errorMessage && (
        <AlertBanner
          type="danger"
          title="Operation Error"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}
      {successMessage && (
        <AlertBanner
          type="success"
          title="Operation Succeeded"
          message={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      {/* 1. TRANSACTION FEED FILE SOURCES */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{ backgroundColor: 'var(--blue-50)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
              <UploadCloud size={20} color="var(--blue-600)" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Bank Transaction Feed
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                LRECL=80 | RECFM=FB | Key: Cols 13–20
              </span>
            </div>
          </div>
          <div style={{ marginTop: '14px' }}>
            <input
              type="file"
              style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', width: '100%' }}
              aria-label="Upload Bank Feed"
            />
          </div>
        </div>

        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{ backgroundColor: 'var(--blue-50)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
              <UploadCloud size={20} color="var(--blue-600)" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Merchant Settlement Feed
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                LRECL=80 | RECFM=FB | Key: Cols 21–28
              </span>
            </div>
          </div>
          <div style={{ marginTop: '14px' }}>
            <input
              type="file"
              style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', width: '100%' }}
              aria-label="Upload Merchant Feed"
            />
          </div>
        </div>

        <div className="fr-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{ backgroundColor: 'var(--blue-50)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
              <UploadCloud size={20} color="var(--blue-600)" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Audit Event Feed
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                LRECL=100 | RECFM=FB | Key: Cols 25–32
              </span>
            </div>
          </div>
          <div style={{ marginTop: '14px' }}>
            <input
              type="file"
              style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', width: '100%' }}
              aria-label="Upload Audit Feed"
            />
          </div>
        </div>
      </div>

      {/* 2. PIPELINE ACTION TOOLBAR */}
      <div className="fr-card" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          onClick={handleValidate}
          disabled={validating}
          className="fr-btn fr-btn-secondary"
          title="Run pre-flight fixed-width record checks"
        >
          <FileCheck size={16} />
          <span>{validating ? 'Validating Feeds...' : 'Validate Feeds'}</span>
        </button>

        <button
          onClick={handleStartRecon}
          disabled={processing || !validationResult}
          className="fr-btn fr-btn-primary"
          title={!validationResult ? 'Please validate feeds first' : 'Run 8-stage financial reconciliation pipeline'}
        >
          <Play size={16} />
          <span>{processing ? 'Executing Batch...' : 'Start Reconciliation Batch'}</span>
        </button>

        <button
          onClick={handleSimulateFailure}
          disabled={simulating || !isSupervisor}
          className="fr-btn fr-btn-danger"
          title={!isSupervisor ? 'Restricted to SUPERVISOR role' : 'Simulate stage mismatch to test self-healing rollback'}
          style={!isSupervisor ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
        >
          <AlertTriangle size={16} />
          <span>{simulating ? 'Simulating...' : 'Simulate Control Failure'}</span>
        </button>

        <button
          onClick={handleTriggerRecovery}
          disabled={recovering || !isSupervisor}
          className="fr-btn fr-btn-secondary"
          style={{ borderColor: 'var(--warning)', color: 'var(--warning-text)', ...( !isSupervisor ? { opacity: 0.6, cursor: 'not-allowed' } : {}) }}
          title={!isSupervisor ? 'Restricted to SUPERVISOR role' : 'Replay affected stage and revalidate controls'}
        >
          <RotateCcw size={16} />
          <span>{recovering ? 'Restoring...' : 'Trigger Self-Healing Recovery'}</span>
        </button>

        <button
          onClick={handleResetPipeline}
          disabled={resetting}
          className="fr-btn fr-btn-secondary"
          style={{ marginLeft: 'auto', color: 'var(--text-secondary)' }}
          title="Reset batch pipeline to initial PENDING state"
        >
          <RefreshCw size={15} />
          <span>{resetting ? 'Resetting...' : 'Reset Pipeline (Pending)'}</span>
        </button>
      </div>

      {/* 3. VALIDATION SUMMARY DETAILS */}
      {validationResult && (
        <div className="fr-card" style={{ padding: '20px 24px', marginBottom: '24px', backgroundColor: 'var(--success-bg)', borderColor: 'var(--success-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success-text)', marginBottom: '8px' }}>
            <CheckCircle2 size={18} />
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>
              Pre-Flight Feed Validation Verified
            </h4>
          </div>
          <ul style={{ margin: 0, paddingLeft: '24px', color: 'var(--success-text)', fontSize: '0.85rem', lineHeight: '1.6' }}>
            {validationResult.validation_messages.map((msg, i) => (
              <li key={i}>{msg}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. FINANCIAL CONTROL CHECKPOINTS GRID */}
      <div className="fr-card" style={{ padding: '20px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <ShieldAlert size={18} color="var(--blue-600)" />
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Financial Control Checkpoints (Stage-Level Telemetry)
          </h3>
        </div>

        <div className="fr-checkpoints-grid">
          {checkpoints.map(chk => {
            const isFailed = chk.control_status === 'FAILED_CONTROL';
            const isHalted = chk.control_status === 'HALTED' || chk.control_status === 'STOPPED';
            const statusCls = getStatusClass(chk.control_status);
            const parsedAlert = parseExceptionReason(chk.error_reason);

            return (
              <div key={chk.id} className={`fr-checkpoint-card status-${statusCls}`}>
                <div className="fr-checkpoint-header">
                  <span className="fr-checkpoint-title">
                    {chk.stage_name}
                  </span>
                  <span className={`fr-checkpoint-badge badge-${statusCls}`}>
                    {chk.control_status}
                  </span>
                </div>

                <div className="fr-checkpoint-metrics">
                  <div className="fr-checkpoint-metric-row">
                    <span className="fr-checkpoint-metric-label">Input Recs:</span>
                    <span className="fr-checkpoint-metric-value">{chk.input_record_count.toLocaleString()}</span>
                  </div>
                  <div className="fr-checkpoint-metric-row">
                    <span className="fr-checkpoint-metric-label">Output Recs:</span>
                    <span className="fr-checkpoint-metric-value">{chk.output_record_count.toLocaleString()}</span>
                  </div>
                  <div className="fr-checkpoint-metric-row">
                    <span className="fr-checkpoint-metric-label">Total Amount:</span>
                    <span className="fr-checkpoint-metric-value">
                      ${chk.output_amount_total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {chk.error_reason && (
                  <div className={`fr-checkpoint-alert-panel ${isFailed ? 'panel-failed' : isHalted ? 'panel-halted' : ''}`}>
                    {parsedAlert && parsedAlert.items.length > 0 ? (
                      <>
                        <div className="fr-checkpoint-alert-header">
                          <AlertTriangle size={13} className="alert-icon" />
                          <span>{parsedAlert.header}</span>
                        </div>
                        <div className="fr-checkpoint-exception-list">
                          {parsedAlert.items.map((item, idx) => (
                            <div key={idx} className="fr-checkpoint-exception-item">
                              <span className="exc-code">{item.code}:</span>
                              <span className="exc-count">{item.count} records</span>
                            </div>
                          ))}
                        </div>
                        {parsedAlert.rawRemainder && (
                          <div style={{ marginTop: '4px', fontSize: '0.68rem', color: '#92400E' }}>
                            {parsedAlert.rawRemainder}
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="fr-checkpoint-alert-text">
                        <AlertTriangle size={13} className="alert-icon" />
                        <span>{chk.error_reason}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {recoveryEvents.length > 0 && (
          <div style={{
            marginTop: '16px',
            backgroundColor: 'var(--panel-subtle)',
            padding: '14px 16px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              <Sparkles size={14} color="var(--blue-600)" />
              <span>Automated Recovery Event Log</span>
            </div>
            {recoveryEvents.map(evt => (
              <div key={evt.id} style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                [{evt.created_at}] <strong>{evt.stage_name}</strong> - {evt.event_type} ({evt.status}): {evt.message}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. MASTER PIPELINE STEPPER */}
      <div className="fr-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Layers size={18} color="var(--blue-600)" />
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Pipeline Execution Stream (Simulated IBM z/OS Jobs)
          </h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {steps.map(step => {
            const statusInfo = getStepStatus(step.stage);
            return (
              <div key={step.num} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                backgroundColor: statusInfo.bg,
                border: `1px solid var(--border-color)`,
                borderRadius: 'var(--radius-md)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{
                    fontWeight: 800,
                    color: 'var(--text-secondary)',
                    fontSize: '0.75rem',
                    backgroundColor: '#E2E8F0',
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)'
                  }}>
                    STEP {step.num}
                  </span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {step.name}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {statusInfo.statusType === 'failed' && <AlertTriangle size={14} color={statusInfo.color} />}
                  {statusInfo.statusType === 'halted' && <Ban size={14} color={statusInfo.color} />}
                  {statusInfo.statusType === 'warning' && <AlertTriangle size={14} color={statusInfo.color} />}
                  {(statusInfo.statusType === 'passed' || statusInfo.statusType === 'recovered') && <CheckCircle2 size={14} color={statusInfo.color} />}
                  {statusInfo.statusType === 'pending' && <Clock size={14} color={statusInfo.color} />}
                  {statusInfo.statusType === 'processing' && <Clock size={14} color={statusInfo.color} />}
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: statusInfo.color }}>
                    {statusInfo.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

