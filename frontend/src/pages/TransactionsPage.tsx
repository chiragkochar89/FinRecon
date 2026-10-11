import React, { useState, useEffect } from 'react';
import {
  getTransactions,
  getTransactionDetail,
  getTransactionLineage,
  explainTransactionDecision,
  getTransactionMatchAnalysis
} from '../services/api';
import {
  TransactionItem,
  TransactionDetail,
  LineageEventModel,
  DecisionExplanationModel,
  MatchAnalysisResponse
} from '../types';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  Search,
  SlidersHorizontal,
  GitBranch,
  Sparkles,
  FileText,
  X,
  Building2,
  Store,
  CheckCircle2,
  ShieldCheck,
  Info
} from 'lucide-react';

export const TransactionsPage: React.FC = () => {
  const [txns, setTxns] = useState<TransactionItem[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedTxn, setSelectedTxn] = useState<TransactionDetail | null>(null);
  
  // Feature B & C modal states
  const [activeTab, setActiveTab] = useState<'detail' | 'lineage' | 'match_analysis'>('detail');
  const [lineageEvents, setLineageEvents] = useState<LineageEventModel[]>([]);
  const [decisionExplanation, setDecisionExplanation] = useState<DecisionExplanationModel | null>(null);
  const [matchAnalysis, setMatchAnalysis] = useState<MatchAnalysisResponse | null>(null);
  const [loadingModal, setLoadingModal] = useState(false);

  useEffect(() => {
    getTransactions(search, statusFilter).then(setTxns).catch(console.error);
  }, [search, statusFilter]);

  const handleRowClick = async (trxnId: string) => {
    setLoadingModal(true);
    setActiveTab('detail');
    try {
      const detail = await getTransactionDetail(trxnId);
      setSelectedTxn(detail);

      // Feature B: Lineage
      try {
        const linRes = await getTransactionLineage(trxnId);
        setLineageEvents(linRes.events || []);
        const expRes = await explainTransactionDecision(trxnId);
        setDecisionExplanation(expRes);
      } catch (e) {
        console.error(e);
      }

      // Feature C: AI Match Analysis
      try {
        const maRes = await getTransactionMatchAnalysis(trxnId);
        setMatchAnalysis(maRes);
      } catch (e) {
        console.error(e);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingModal(false);
    }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      <PageHeader
        title="Transaction Records & Lineage Provenance"
        description="Filter all reconciled transactions, inspect stage-by-stage data lineage, explain deterministic decisions, and review AI match scoring."
        batchId="FINREC-20260922-001"
        mode="LOCAL_DEMO"
      />

      {/* FILTER & SEARCH TOOLBAR */}
      <div className="fr-card" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '260px' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search Transaction ID or Account (e.g. TXN10001 or ACC100000001)..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="fr-input"
              style={{ paddingLeft: '36px' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <SlidersHorizontal size={16} color="var(--text-secondary)" />
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="fr-select"
              aria-label="Filter by Status"
            >
              <option value="">All Reconciliation Statuses</option>
              <option value="MATCHED">MATCHED</option>
              <option value="AMOUNT-MISMATCH">AMOUNT-MISMATCH</option>
              <option value="STATUS-MISMATCH">STATUS-MISMATCH</option>
            </select>
          </div>

          <div style={{
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            fontWeight: 600,
            marginLeft: 'auto'
          }}>
            Showing <strong>{txns.length}</strong> records
          </div>
        </div>
      </div>

      {/* DATA TABLE */}
      <div className="fr-table-container">
        <table className="fr-data-table">
          <thead>
            <tr>
              <th>Transaction ID</th>
              <th>Account ID</th>
              <th className="fr-money">Recon Amount ($)</th>
              <th>Bank Status</th>
              <th>Merchant Status</th>
              <th>Recon Status</th>
              <th>Reason Code</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {txns.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No transactions match the selected filter criteria.
                </td>
              </tr>
            ) : (
              txns.map(t => (
                <tr key={t.trxn_id}>
                  <td>
                    <button
                      onClick={() => handleRowClick(t.trxn_id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        fontWeight: 700,
                        color: 'var(--blue-600)',
                        cursor: 'pointer',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      {t.trxn_id}
                    </button>
                  </td>
                  <td className="fr-mono" style={{ color: 'var(--text-secondary)' }}>
                    {t.acct_no}
                  </td>
                  <td className="fr-money" style={{ color: 'var(--text-primary)' }}>
                    ${t.amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td>
                    <StatusBadge status={t.bank_status} size="sm" />
                  </td>
                  <td>
                    <StatusBadge status={t.merch_status} size="sm" />
                  </td>
                  <td>
                    <StatusBadge status={t.recon_result} size="sm" />
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '11px' }}>
                    {t.exception_code}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => handleRowClick(t.trxn_id)}
                      className="fr-btn fr-btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '11px' }}
                    >
                      <GitBranch size={12} color="var(--blue-600)" />
                      <span>Lineage & Match</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* DETAIL, LINEAGE, AND MATCH ANALYSIS MODAL */}
      {selectedTxn && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(13, 24, 41, 0.6)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(2px)'
        }}>
          <div className="fr-card" style={{
            width: '780px',
            maxWidth: '95%',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-lg)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#F8FAFC'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Transaction Provenance: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--blue-600)' }}>{selectedTxn.transaction_id}</span>
                  </h3>
                  <StatusBadge status={selectedTxn.recon_result} size="sm" />
                </div>
                <p style={{ margin: '2px 0 0', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Deterministic outcome: <strong>{selectedTxn.reason_code}</strong> | Variance: <strong>${selectedTxn.amount_difference.toFixed(2)}</strong>
                </p>
              </div>

              <button
                onClick={() => setSelectedTxn(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '4px',
                  borderRadius: '4px'
                }}
                aria-label="Close modal"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-color)',
              padding: '0 24px',
              backgroundColor: '#FFFFFF'
            }}>
              <button
                onClick={() => setActiveTab('detail')}
                style={{
                  padding: '12px 16px',
                  border: 'none',
                  background: 'none',
                  borderBottom: activeTab === 'detail' ? '2px solid var(--blue-600)' : '2px solid transparent',
                  fontWeight: activeTab === 'detail' ? 700 : 500,
                  color: activeTab === 'detail' ? 'var(--blue-600)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.85rem'
                }}
              >
                <FileText size={15} />
                <span>Source Records</span>
              </button>

              <button
                onClick={() => setActiveTab('lineage')}
                style={{
                  padding: '12px 16px',
                  border: 'none',
                  background: 'none',
                  borderBottom: activeTab === 'lineage' ? '2px solid var(--blue-600)' : '2px solid transparent',
                  fontWeight: activeTab === 'lineage' ? 700 : 500,
                  color: activeTab === 'lineage' ? 'var(--blue-600)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.85rem'
                }}
              >
                <GitBranch size={15} />
                <span>Lineage Provenance (Feature B)</span>
              </button>

              <button
                onClick={() => setActiveTab('match_analysis')}
                style={{
                  padding: '12px 16px',
                  border: 'none',
                  background: 'none',
                  borderBottom: activeTab === 'match_analysis' ? '2px solid var(--blue-600)' : '2px solid transparent',
                  fontWeight: activeTab === 'match_analysis' ? 700 : 500,
                  color: activeTab === 'match_analysis' ? 'var(--blue-600)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.85rem'
                }}
              >
                <Sparkles size={15} />
                <span>AI Hybrid Match (Feature C)</span>
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', overflowY: 'auto' }}>
              {/* Tab 1: Source Records */}
              {activeTab === 'detail' && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                    <div style={{ backgroundColor: 'var(--panel-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--blue-600)', marginBottom: '10px' }}>
                        <Building2 size={16} />
                        <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase' }}>Bank Source Feed</h4>
                      </div>
                      <div style={{ fontSize: '0.85rem', marginBottom: '6px' }}>Account: <strong className="fr-mono">{selectedTxn.bank_record.acct_no}</strong></div>
                      <div style={{ fontSize: '0.85rem', marginBottom: '6px' }}>Amount: <strong>${selectedTxn.bank_record.amt.toFixed(2)}</strong></div>
                      <div style={{ fontSize: '0.85rem', marginBottom: '6px' }}>Status: <StatusBadge status={selectedTxn.bank_record.status} size="sm" /></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>LRECL Key: {selectedTxn.bank_record.key_pos}</div>
                    </div>

                    <div style={{ backgroundColor: 'var(--panel-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#16A34A', marginBottom: '10px' }}>
                        <Store size={16} />
                        <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase' }}>Merchant Source Feed</h4>
                      </div>
                      <div style={{ fontSize: '0.85rem', marginBottom: '6px' }}>Merchant ID: <strong className="fr-mono">{selectedTxn.merch_record.merch_id}</strong></div>
                      <div style={{ fontSize: '0.85rem', marginBottom: '6px' }}>Amount: <strong>${selectedTxn.merch_record.amt.toFixed(2)}</strong></div>
                      <div style={{ fontSize: '0.85rem', marginBottom: '6px' }}>Status: <StatusBadge status={selectedTxn.merch_record.status} size="sm" /></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>LRECL Key: {selectedTxn.merch_record.key_pos}</div>
                    </div>
                  </div>

                  <div style={{
                    backgroundColor: 'var(--info-bg)',
                    border: '1px solid var(--info-border)',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--info-text)',
                    fontSize: '0.85rem'
                  }}>
                    <strong>Reconciliation Status:</strong> {selectedTxn.recon_result} | Reason: {selectedTxn.reason_code} | Variance Exposure: ${selectedTxn.amount_difference.toFixed(2)}
                  </div>
                </div>
              )}

              {/* Tab 2: Feature B Lineage Provenance */}
              {activeTab === 'lineage' && (
                <div>
                  {decisionExplanation && (
                    <div style={{
                      backgroundColor: 'var(--panel-subtle)',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-color)',
                      marginBottom: '16px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '4px' }}>
                        <ShieldCheck size={16} color="var(--blue-600)" />
                        <span>Deterministic Decision Explanation</span>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                        {decisionExplanation.decision}
                      </p>
                    </div>
                  )}

                  <h4 style={{ margin: '0 0 12px', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                    End-to-End Lineage Timeline
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {lineageEvents.map(evt => (
                      <div key={evt.id} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '10px 14px',
                        backgroundColor: '#F8FAFC',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.8rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontWeight: 800, color: 'var(--blue-600)' }}>● {evt.stage_name}</span>
                          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>[{evt.event_type}]</span>
                        </div>
                        <span style={{ color: 'var(--text-secondary)' }}>
                          Source: {evt.source_system} ({evt.actor})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: Feature C AI Match Analysis */}
              {activeTab === 'match_analysis' && (
                <div>
                  <div style={{
                    backgroundColor: 'var(--panel-subtle)',
                    padding: '14px 16px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                    marginBottom: '16px'
                  }}>
                    <h4 style={{ margin: '0 0 6px', fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      Mainframe Deterministic Match Result (Primary Authority)
                    </h4>
                    <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {matchAnalysis?.deterministic_result || 'Exact match processing satisfied'}
                    </p>
                  </div>

                  {matchAnalysis?.intelligent_analysis ? (
                    <div style={{
                      backgroundColor: 'var(--success-bg)',
                      border: '1px solid var(--success-border)',
                      padding: '16px',
                      borderRadius: 'var(--radius-md)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success-text)', fontWeight: 700, fontSize: '0.85rem' }}>
                          <Sparkles size={16} />
                          <span>Secondary AI Hybrid Match Engine (Advisory Only)</span>
                        </div>
                        <span style={{
                          backgroundColor: '#059669',
                          color: '#FFFFFF',
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.75rem',
                          fontWeight: 800
                        }}>
                          {matchAnalysis.intelligent_analysis.confidence_classification} ({Math.round(matchAnalysis.intelligent_analysis.confidence_score * 100)}%)
                        </span>
                      </div>

                      <div style={{ fontSize: '0.85rem', color: 'var(--success-text)', marginBottom: '14px' }}>
                        Candidate Transaction: <strong className="fr-mono">{matchAnalysis.intelligent_analysis.candidate_transaction_id}</strong> | Recommendation: <strong>{matchAnalysis.intelligent_analysis.decision}</strong>
                      </div>

                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '8px',
                        fontSize: '0.75rem',
                        color: 'var(--success-text)',
                        marginBottom: '14px'
                      }}>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.7)', padding: '6px 8px', borderRadius: '4px' }}>Amount: <strong>{Math.round(matchAnalysis.intelligent_analysis.feature_scores.amount_similarity * 100)}%</strong></div>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.7)', padding: '6px 8px', borderRadius: '4px' }}>Date: <strong>{Math.round(matchAnalysis.intelligent_analysis.feature_scores.date_similarity * 100)}%</strong></div>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.7)', padding: '6px 8px', borderRadius: '4px' }}>Merchant: <strong>{Math.round(matchAnalysis.intelligent_analysis.feature_scores.merchant_similarity * 100)}%</strong></div>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.7)', padding: '6px 8px', borderRadius: '4px' }}>Reference: <strong>{Math.round(matchAnalysis.intelligent_analysis.feature_scores.reference_similarity * 100)}%</strong></div>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.7)', padding: '6px 8px', borderRadius: '4px' }}>Account: <strong>{Math.round(matchAnalysis.intelligent_analysis.feature_scores.account_similarity * 100)}%</strong></div>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.7)', padding: '6px 8px', borderRadius: '4px' }}>Status: <strong>{Math.round(matchAnalysis.intelligent_analysis.feature_scores.status_similarity * 100)}%</strong></div>
                      </div>

                      <div style={{
                        fontSize: '0.75rem',
                        color: 'var(--success-text)',
                        borderTop: '1px solid var(--success-border)',
                        paddingTop: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        <Info size={14} />
                        <span><strong>Governance Safeguard:</strong> This AI match score does NOT override the authoritative COBOL result without Supervisor triage action.</span>
                      </div>
                    </div>
                  ) : (
                    <div style={{
                      backgroundColor: 'var(--panel-subtle)',
                      padding: '16px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-secondary)',
                      fontSize: '0.85rem'
                    }}>
                      Deterministic exact match satisfied COBOL reconciliation rules. Secondary AI candidate scoring was bypassed.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
