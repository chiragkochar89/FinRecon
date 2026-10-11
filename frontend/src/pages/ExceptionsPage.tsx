import React, { useState, useEffect } from 'react';
import {
  getExceptions,
  getExceptionsSummary,
  assignException,
  addExceptionNote,
  updateExceptionStatus,
  getExceptionAuditHistory
} from '../services/api';
import {
  ExceptionModel,
  ExceptionSummaryModel,
  AuditEventItem,
  TriageStatus,
  ResolutionCode
} from '../types';
import { PageHeader } from '../components/common/PageHeader';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { AlertBanner } from '../components/common/AlertBanner';
import {
  AlertTriangle,
  Search,
  SlidersHorizontal,
  X,
  UserCheck,
  MessageSquare,
  History,
  CheckCircle,
  XCircle,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

export const ExceptionsPage: React.FC = () => {
  const [exceptions, setExceptions] = useState<ExceptionModel[]>([]);
  const [summary, setSummary] = useState<ExceptionSummaryModel | null>(null);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [severityFilter, setSeverityFilter] = useState('');
  const [reasonFilter, setReasonFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Exception Drawer State
  const [selectedException, setSelectedException] = useState<ExceptionModel | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([]);
  const [assigneeInput, setAssigneeInput] = useState('');
  const [newNoteInput, setNewNoteInput] = useState('');

  // Action Modals State
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [resolutionCode, setResolutionCode] = useState<ResolutionCode>('RESOLVED_VALID_TRANSACTION');
  const [rejectionCode, setRejectionCode] = useState<ResolutionCode>('REJECTED_FALSE_POSITIVE');
  const [actionNotes, setActionNotes] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [excs, sum] = await Promise.all([
        getExceptions({
          severity: severityFilter || undefined,
          reason_code: reasonFilter || undefined,
          triage_status: statusFilter || undefined,
          search: searchQuery || undefined
        }),
        getExceptionsSummary('FINREC-20260922-001')
      ]);
      setExceptions(excs);
      setSummary(sum);
    } catch (err) {
      console.error('Error loading exceptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [severityFilter, reasonFilter, statusFilter, searchQuery]);

  const handleSelectException = async (exc: ExceptionModel) => {
    setSelectedException(exc);
    setAssigneeInput(exc.assigned_to || '');
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const history = await getExceptionAuditHistory(exc.exception_id);
      setAuditEvents(history);
    } catch (err) {
      setAuditEvents([]);
    }
  };

  const handleAssign = async () => {
    if (!selectedException) return;
    if (!assigneeInput.trim()) {
      setErrorMessage('Assignee name cannot be empty.');
      return;
    }
    setErrorMessage(null);
    try {
      const updated = await assignException(selectedException.exception_id, assigneeInput.trim());
      setSelectedException(updated);
      setSuccessMessage(`Exception successfully assigned to ${assigneeInput.trim()}.`);
      await loadData();
      const history = await getExceptionAuditHistory(selectedException.exception_id);
      setAuditEvents(history);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to assign exception.');
    }
  };

  const handleAddNote = async () => {
    if (!selectedException) return;
    if (!newNoteInput.trim()) {
      setErrorMessage('Note content cannot be empty.');
      return;
    }
    setErrorMessage(null);
    const activeUser = localStorage.getItem('finrecon_user') || 'ANALYST_01';
    try {
      await addExceptionNote(selectedException.exception_id, newNoteInput.trim(), activeUser);
      setNewNoteInput('');
      setSuccessMessage('Investigation note added to immutable audit log.');
      const updated = await getExceptions({ search: selectedException.exception_id });
      if (updated.length > 0) setSelectedException(updated[0]);
      await loadData();
      const history = await getExceptionAuditHistory(selectedException.exception_id);
      setAuditEvents(history);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to add note.');
    }
  };

  const handleStartReview = async () => {
    if (!selectedException) return;
    setErrorMessage(null);
    try {
      const updated = await updateExceptionStatus(selectedException.exception_id, 'IN_REVIEW');
      setSelectedException(updated);
      setSuccessMessage('Exception status moved to IN_REVIEW.');
      await loadData();
      const history = await getExceptionAuditHistory(selectedException.exception_id);
      setAuditEvents(history);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update status.');
    }
  };

  const handleResolveSubmit = async () => {
    if (!selectedException) return;
    if (!actionNotes.trim()) {
      setErrorMessage('Resolution notes are required.');
      return;
    }
    setErrorMessage(null);
    try {
      const updated = await updateExceptionStatus(
        selectedException.exception_id,
        'RESOLVED',
        resolutionCode,
        actionNotes.trim()
      );
      setSelectedException(updated);
      setIsResolveModalOpen(false);
      setActionNotes('');
      setSuccessMessage(`Case resolved with code ${resolutionCode}.`);
      await loadData();
      const history = await getExceptionAuditHistory(selectedException.exception_id);
      setAuditEvents(history);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to resolve exception.');
    }
  };

  const handleRejectSubmit = async () => {
    if (!selectedException) return;
    if (!actionNotes.trim()) {
      setErrorMessage('Rejection notes are required.');
      return;
    }
    setErrorMessage(null);
    try {
      const updated = await updateExceptionStatus(
        selectedException.exception_id,
        'REJECTED',
        rejectionCode,
        actionNotes.trim()
      );
      setSelectedException(updated);
      setIsRejectModalOpen(false);
      setActionNotes('');
      setSuccessMessage(`Case rejected with code ${rejectionCode}.`);
      await loadData();
      const history = await getExceptionAuditHistory(selectedException.exception_id);
      setAuditEvents(history);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reject exception.');
    }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="Exception Management & Triage Workspace"
        description="Operational triage layer for transaction discrepancies. Source reconciliation calculations remain immutable."
        batchId="FINREC-20260922-001"
        mode="LOCAL_DEMO"
      />

      {/* SUMMARY STATS GRID */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '14px',
          marginBottom: '24px'
        }}>
          <MetricCard
            label="Total Exceptions"
            value={summary.total_exceptions}
            subtext="Authoritative count"
            icon={<AlertTriangle size={18} color="var(--danger)" />}
            variant="default"
          />

          <MetricCard
            label="Critical Exposure"
            value={summary.critical_count}
            subtext="Diff >= $500.00"
            variant="danger"
          />

          <MetricCard
            label="High Severity"
            value={summary.high_count}
            subtext="Status / Amount mismatch"
            variant="warning"
          />

          <MetricCard
            label="Open Cases"
            value={summary.unassigned_count + summary.in_review_count}
            subtext={`${summary.unassigned_count} unassigned`}
            variant="info"
          />

          <MetricCard
            label="Resolved Cases"
            value={summary.resolved_count}
            subtext="Closed with code"
            variant="success"
          />

          <MetricCard
            label="Open Financial Exp"
            value={`$${summary.open_financial_exposure.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
            subtext="Net pending exposure"
            variant="danger"
          />
        </div>
      )}

      {/* FILTER TOOLBAR */}
      <div className="fr-card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search Exception ID, Transaction ID, Assignee..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="fr-input"
              style={{ paddingLeft: '36px' }}
            />
          </div>

          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="fr-select"
            aria-label="Filter by Severity"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          <select
            value={reasonFilter}
            onChange={e => setReasonFilter(e.target.value)}
            className="fr-select"
            aria-label="Filter by Reason Code"
          >
            <option value="">All Reason Codes</option>
            <option value="RCN-101">RCN-101 (Amount Mismatch)</option>
            <option value="RCN-102">RCN-102 (Status Mismatch)</option>
            <option value="RCN-103">RCN-103 (Missing in Bank)</option>
            <option value="RCN-104">RCN-104 (Missing in Merch)</option>
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="fr-select"
            aria-label="Filter by Triage Status"
          >
            <option value="">All Triage Statuses</option>
            <option value="UNASSIGNED">UNASSIGNED</option>
            <option value="IN_REVIEW">IN_REVIEW</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, marginLeft: 'auto' }}>
            Showing <strong>{exceptions.length}</strong> exceptions
          </div>
        </div>
      </div>

      {/* TWO-COLUMN LAYOUT: EXCEPTIONS TABLE + INSPECTION DRAWER */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: selectedException ? '1fr 440px' : '1fr',
        gap: '20px',
        alignItems: 'start'
      }}>
        {/* EXCEPTIONS DATA TABLE */}
        <div className="fr-table-container">
          <table className="fr-data-table">
            <thead>
              <tr>
                <th>Exception ID</th>
                <th>Transaction ID</th>
                <th>Severity</th>
                <th>Reason</th>
                <th className="fr-money">Discrepancy ($)</th>
                <th>Triage Status</th>
                <th>Assignee</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {exceptions.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No exceptions match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                exceptions.map(e => {
                  const isSelected = selectedException?.exception_id === e.exception_id;
                  return (
                    <tr
                      key={e.exception_id}
                      onClick={() => handleSelectException(e)}
                      style={{
                        backgroundColor: isSelected ? 'var(--blue-50)' : undefined,
                        cursor: 'pointer'
                      }}
                    >
                      <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                        {e.exception_id}
                      </td>
                      <td style={{ color: 'var(--blue-600)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                        {e.transaction_id}
                      </td>
                      <td>
                        <StatusBadge status={e.severity} size="sm" />
                      </td>
                      <td style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-secondary)' }}>
                        {e.reason_code}
                      </td>
                      <td className="fr-money" style={{ color: e.amount_difference > 0 ? 'var(--danger)' : 'var(--success)' }}>
                        ${e.amount_difference.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td>
                        <StatusBadge status={e.triage_status} size="sm" />
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>
                        {e.assigned_to || 'Unassigned'}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          onClick={evt => {
                            evt.stopPropagation();
                            handleSelectException(e);
                          }}
                          className="fr-btn fr-btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '11px' }}
                        >
                          <span>Inspect</span>
                          <ArrowRight size={12} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* SELECTED EXCEPTION DRAWER */}
        {selectedException && (
          <div className="fr-card" style={{ padding: '20px', position: 'sticky', top: '24px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--border-color)',
              paddingBottom: '12px',
              marginBottom: '16px'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    {selectedException.exception_id}
                  </h3>
                  <StatusBadge status={selectedException.triage_status} size="sm" />
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--blue-600)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                  TXN: {selectedException.transaction_id}
                </span>
              </div>

              <button
                onClick={() => setSelectedException(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '4px'
                }}
                aria-label="Close drawer"
              >
                <X size={18} />
              </button>
            </div>

            {errorMessage && (
              <AlertBanner
                type="danger"
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

            {/* Read-Only Financial Metadata */}
            <div style={{
              backgroundColor: 'var(--panel-subtle)',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              marginBottom: '16px',
              fontSize: '0.8rem'
            }}>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <ShieldAlert size={12} />
                <span>Reconciliation Metadata (Read-Only)</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>Reason Code: <strong>{selectedException.reason_code}</strong></div>
                <div>Severity: <StatusBadge status={selectedException.severity} size="sm" /></div>
                <div>Bank Amt: <strong>${selectedException.bank_amount.toFixed(2)}</strong> ({selectedException.bank_status})</div>
                <div>Merch Amt: <strong>${selectedException.merchant_amount.toFixed(2)}</strong> ({selectedException.merchant_status})</div>
                <div style={{ gridColumn: 'span 2', color: 'var(--danger)', fontWeight: 700 }}>
                  Discrepancy Difference: ${selectedException.amount_difference.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Triage Assignment */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                Assign Case to Analyst
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Analyst ID (e.g. ANALYST_01)..."
                  value={assigneeInput}
                  onChange={e => setAssigneeInput(e.target.value)}
                  className="fr-input"
                  style={{ fontSize: '0.8rem', padding: '6px 10px' }}
                />
                <button
                  onClick={handleAssign}
                  className="fr-btn fr-btn-primary"
                  style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                >
                  <UserCheck size={14} />
                  <span>Assign</span>
                </button>
              </div>
            </div>

            {/* Triage Status Transitions */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                Operational Triage Actions
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {selectedException.triage_status === 'UNASSIGNED' && (
                  <button
                    onClick={handleStartReview}
                    className="fr-btn fr-btn-primary"
                    style={{ width: '100%' }}
                  >
                    <span>Start Review (Move to In Review)</span>
                  </button>
                )}

                {selectedException.triage_status === 'IN_REVIEW' && (
                  <>
                    <button
                      onClick={() => setIsResolveModalOpen(true)}
                      className="fr-btn"
                      style={{ flex: 1, backgroundColor: 'var(--success)', color: '#FFF' }}
                    >
                      <CheckCircle size={14} />
                      <span>Resolve Case</span>
                    </button>
                    <button
                      onClick={() => setIsRejectModalOpen(true)}
                      className="fr-btn fr-btn-danger"
                      style={{ flex: 1 }}
                    >
                      <XCircle size={14} />
                      <span>Reject Case</span>
                    </button>
                  </>
                )}

                {(selectedException.triage_status === 'RESOLVED' || selectedException.triage_status === 'REJECTED') && (
                  <div style={{
                    backgroundColor: 'var(--panel-subtle)',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                    width: '100%',
                    fontSize: '0.8rem'
                  }}>
                    <div><strong>Disposition:</strong> {selectedException.resolution_code}</div>
                    <div style={{ marginTop: '2px', color: 'var(--text-secondary)' }}>
                      <strong>Notes:</strong> {selectedException.resolution_notes}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Investigation Notes */}
            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '14px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                <MessageSquare size={14} color="var(--blue-600)" />
                <span>Investigation Notes ({selectedException.notes?.length || 0})</span>
              </div>

              <div style={{
                maxHeight: '120px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                marginBottom: '8px'
              }}>
                {selectedException.notes && selectedException.notes.length > 0 ? (
                  selectedException.notes.map(n => (
                    <div key={n.note_id} style={{
                      backgroundColor: 'var(--panel-subtle)',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.75rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontWeight: 600 }}>
                        <span>{n.author}</span>
                        <span>{n.timestamp}</span>
                      </div>
                      <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>{n.note_text}</div>
                    </div>
                  ))
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No notes recorded.</span>
                )}
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Add note..."
                  value={newNoteInput}
                  onChange={e => setNewNoteInput(e.target.value)}
                  className="fr-input"
                  style={{ fontSize: '0.75rem', padding: '6px 10px' }}
                />
                <button
                  onClick={handleAddNote}
                  className="fr-btn fr-btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '6px 10px' }}
                >
                  Post
                </button>
              </div>
            </div>

            {/* Audit History Timeline */}
            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                <History size={14} color="var(--blue-600)" />
                <span>Audit Trail History</span>
              </div>

              <div style={{ maxHeight: '140px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {auditEvents.map(evt => (
                  <div key={evt.event_id} style={{
                    fontSize: '0.75rem',
                    borderLeft: '3px solid var(--blue-600)',
                    paddingLeft: '8px',
                    color: 'var(--text-secondary)'
                  }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      {evt.event_type} — <span style={{ color: 'var(--blue-600)' }}>{evt.actor}</span>
                    </div>
                    <div style={{ fontSize: '0.7rem' }}>{evt.details}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* RESOLVE CASE MODAL */}
      {isResolveModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(13, 24, 41, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(2px)'
        }}>
          <div className="fr-card" style={{ width: '460px', maxWidth: '90%', padding: '24px' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--success)' }}>
              Resolve Exception Case
            </h3>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '6px' }}>
                Resolution Reason Code:
              </label>
              <select
                value={resolutionCode}
                onChange={e => setResolutionCode(e.target.value as ResolutionCode)}
                className="fr-select"
                style={{ width: '100%' }}
              >
                <option value="RESOLVED_VALID_TRANSACTION">RESOLVED_VALID_TRANSACTION</option>
                <option value="RESOLVED_DATA_CORRECTION">RESOLVED_DATA_CORRECTION</option>
                <option value="RESOLVED_DUPLICATE_CONFIRMED">RESOLVED_DUPLICATE_CONFIRMED</option>
                <option value="RESOLVED_SOURCE_DELAY">RESOLVED_SOURCE_DELAY</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '6px' }}>
                Resolution Notes (Required for Audit Trail):
              </label>
              <textarea
                rows={3}
                placeholder="Explain justification and resolution details..."
                value={actionNotes}
                onChange={e => setActionNotes(e.target.value)}
                className="fr-input"
                style={{ resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => setIsResolveModalOpen(false)}
                className="fr-btn fr-btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveSubmit}
                className="fr-btn"
                style={{ backgroundColor: 'var(--success)', color: '#FFF' }}
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REJECT CASE MODAL */}
      {isRejectModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(13, 24, 41, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(2px)'
        }}>
          <div className="fr-card" style={{ width: '460px', maxWidth: '90%', padding: '24px' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '1.1rem', fontWeight: 700, color: 'var(--danger)' }}>
              Reject Exception Case
            </h3>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '6px' }}>
                Rejection Reason Code:
              </label>
              <select
                value={rejectionCode}
                onChange={e => setRejectionCode(e.target.value as ResolutionCode)}
                className="fr-select"
                style={{ width: '100%' }}
              >
                <option value="REJECTED_FALSE_POSITIVE">REJECTED_FALSE_POSITIVE</option>
                <option value="REJECTED_INVALID_CASE">REJECTED_INVALID_CASE</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '6px' }}>
                Rejection Notes (Required for Audit Trail):
              </label>
              <textarea
                rows={3}
                placeholder="Explain justification for rejecting case..."
                value={actionNotes}
                onChange={e => setActionNotes(e.target.value)}
                className="fr-input"
                style={{ resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => setIsRejectModalOpen(false)}
                className="fr-btn fr-btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectSubmit}
                className="fr-btn fr-btn-danger"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
