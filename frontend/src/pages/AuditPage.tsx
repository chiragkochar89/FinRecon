import React, { useState, useEffect } from 'react';
import { getBatchAudit, getAllAuditEvents } from '../services/api';
import { AuditLogItem, AuditEventItem } from '../types';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  History,
  Search,
  SlidersHorizontal,
  ShieldCheck,
  Cpu,
  Layers,
  User,
  Clock,
  ShieldAlert
} from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'triage' | 'batch'>('triage');
  const [batchLogs, setBatchLogs] = useState<AuditLogItem[]>([]);
  const [triageEvents, setTriageEvents] = useState<AuditEventItem[]>([]);
  
  // Filter States
  const [actorFilter, setActorFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    try {
      const [bLogs, tEvts] = await Promise.all([
        getBatchAudit('FINREC-20260922-001'),
        getAllAuditEvents(actorFilter || undefined, roleFilter || undefined, eventTypeFilter || undefined)
      ]);
      setBatchLogs(bLogs);
      setTriageEvents(tEvts);
    } catch (err) {
      console.error('Error loading audit data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, [actorFilter, roleFilter, eventTypeFilter]);

  const filteredTriageEvents = triageEvents.filter(e => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const match = (
        e.event_id.toLowerCase().includes(q) ||
        e.exception_id.toLowerCase().includes(q) ||
        e.actor.toLowerCase().includes(q) ||
        e.details.toLowerCase().includes(q)
      );
      if (!match) return false;
    }
    return true;
  });

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="Enterprise Audit Trail & Immutable Event Logs"
        description="Comprehensive audit provenance covering append-only SQLite operational triage events and simulated batch pipeline steps."
        batchId="FINREC-20260922-001"
        mode="LOCAL_DEMO"
      />

      {/* TABS SELECTOR */}
      <div style={{
        display: 'flex',
        gap: '8px',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '20px'
      }}>
        <button
          onClick={() => setActiveTab('triage')}
          style={{
            padding: '10px 18px',
            border: 'none',
            background: 'none',
            borderBottom: activeTab === 'triage' ? '2px solid var(--blue-600)' : '2px solid transparent',
            fontWeight: activeTab === 'triage' ? 700 : 500,
            color: activeTab === 'triage' ? 'var(--blue-600)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <History size={16} />
          <span>Operational Triage Audit Events ({filteredTriageEvents.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('batch')}
          style={{
            padding: '10px 18px',
            border: 'none',
            background: 'none',
            borderBottom: activeTab === 'batch' ? '2px solid var(--blue-600)' : '2px solid transparent',
            fontWeight: activeTab === 'batch' ? 700 : 500,
            color: activeTab === 'batch' ? 'var(--blue-600)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Layers size={16} />
          <span>Batch Step Execution Logs ({batchLogs.length})</span>
        </button>
      </div>

      {/* TAB 1: OPERATIONAL TRIAGE AUDIT EVENTS */}
      {activeTab === 'triage' && (
        <div>
          {/* FILTER TOOLBAR */}
          <div className="fr-card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
                <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '10px' }} />
                <input
                  type="text"
                  placeholder="Search Event ID, Exception ID, Details..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="fr-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>

              <input
                type="text"
                placeholder="Filter by Actor..."
                value={actorFilter}
                onChange={e => setActorFilter(e.target.value)}
                className="fr-input"
                style={{ width: '160px' }}
              />

              <select
                value={roleFilter}
                onChange={e => setRoleFilter(e.target.value)}
                className="fr-select"
                aria-label="Filter by Role"
              >
                <option value="">All Roles</option>
                <option value="ANALYST">ANALYST</option>
                <option value="SUPERVISOR">SUPERVISOR</option>
                <option value="SYSTEM">SYSTEM</option>
              </select>

              <select
                value={eventTypeFilter}
                onChange={e => setEventTypeFilter(e.target.value)}
                className="fr-select"
                aria-label="Filter by Event Type"
              >
                <option value="">All Event Types</option>
                <option value="EXCEPTION_CREATED">EXCEPTION_CREATED</option>
                <option value="EXCEPTION_ASSIGNED">EXCEPTION_ASSIGNED</option>
                <option value="STATUS_CHANGED">STATUS_CHANGED</option>
                <option value="NOTE_ADDED">NOTE_ADDED</option>
                <option value="EXCEPTION_RESOLVED">EXCEPTION_RESOLVED</option>
                <option value="EXCEPTION_REJECTED">EXCEPTION_REJECTED</option>
                <option value="REPORT_EXPORTED">REPORT_EXPORTED</option>
                <option value="SECURITY_DENIED">SECURITY_DENIED</option>
              </select>
            </div>
          </div>

          {/* TRIAGE AUDIT DATA TABLE */}
          <div className="fr-table-container">
            <table className="fr-data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event ID</th>
                  <th>Exception ID</th>
                  <th>Event Type</th>
                  <th>Actor</th>
                  <th>Role</th>
                  <th>Action Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredTriageEvents.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                      No audit events match the specified filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredTriageEvents.map(e => {
                    const isDenied = e.event_type === 'SECURITY_DENIED';
                    return (
                      <tr key={e.event_id} style={{ backgroundColor: isDenied ? 'var(--danger-bg)' : undefined }}>
                        <td style={{ color: 'var(--text-secondary)', fontSize: '11px', whiteSpace: 'nowrap' }}>
                          {e.timestamp}
                        </td>
                        <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                          {e.event_id}
                        </td>
                        <td style={{ fontWeight: 700, color: 'var(--blue-600)', fontFamily: 'var(--font-mono)' }}>
                          {e.exception_id}
                        </td>
                        <td>
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '10px',
                            fontWeight: 700,
                            backgroundColor: isDenied ? 'var(--danger-bg)' : 'var(--blue-50)',
                            color: isDenied ? 'var(--danger-text)' : 'var(--info-text)',
                            border: `1px solid ${isDenied ? 'var(--danger-border)' : 'var(--info-border)'}`
                          }}>
                            {e.event_type}
                          </span>
                        </td>
                        <td style={{ fontWeight: 600 }}>
                          {e.actor}
                        </td>
                        <td>
                          <span style={{
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 700,
                            backgroundColor: e.role === 'SUPERVISOR' ? '#EFF6FF' : '#F1F5F9',
                            color: e.role === 'SUPERVISOR' ? '#1D4ED8' : '#475569'
                          }}>
                            {e.role}
                          </span>
                        </td>
                        <td style={{ color: isDenied ? 'var(--danger-text)' : 'var(--text-primary)', maxWidth: '380px' }}>
                          {e.details}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: MAINFRAME BATCH EXECUTION LOGS */}
      {activeTab === 'batch' && (
        <div className="fr-table-container">
          <table className="fr-data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Step Code</th>
                <th>Batch Job / Program Name</th>
                <th>Execution Status</th>
                <th>Return Code</th>
              </tr>
            </thead>
            <tbody>
              {batchLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No batch execution steps logged for this batch run.
                  </td>
                </tr>
              ) : (
                batchLogs.map((l, idx) => (
                  <tr key={idx}>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '11px', whiteSpace: 'nowrap' }}>
                      {l.timestamp}
                    </td>
                    <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      {l.step}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {l.name}
                    </td>
                    <td>
                      <StatusBadge status={l.status} size="sm" />
                    </td>
                    <td style={{ fontWeight: 700, color: l.rc === 0 ? 'var(--success)' : 'var(--warning)' }}>
                      RC={l.rc < 10 ? `0${l.rc}` : l.rc}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
