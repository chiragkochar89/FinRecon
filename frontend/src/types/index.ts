export type ExecutionMode = 'LOCAL_DEMO' | 'REAL_MAINFRAME';

export type BatchStatus = 
  | 'RECEIVED'
  | 'VALIDATING'
  | 'PROCESSING'
  | 'RECONCILING'
  | 'VALIDATING_TOTALS'
  | 'COMPLETED'
  | 'COMPLETED_WITH_EXCEPTIONS'
  | 'FAILED';

export interface SystemHealth {
  status: string;
  mode: ExecutionMode;
  service: string;
  version: string;
}

export interface FileValidationResult {
  valid: boolean;
  bank_record_count: number;
  merch_record_count: number;
  audit_record_count: number;
  validation_messages: string[];
}

export interface ReportSummary {
  batch_id: string;
  process_date: string;
  total_bank_records: number;
  total_merch_records: number;
  matched_count: number;
  amount_mismatch_count: number;
  status_mismatch_count: number;
  missing_bank_count: number;
  missing_merch_count: number;
  total_exceptions: number;
  matched_amount: number;
  total_discrepancy_amount: number;
  final_status: string;
  report_text: string;
}

export interface ControlTotalResult {
  input_record_count: number;
  output_record_count: number;
  count_status: string;
  input_total_amount: number;
  output_total_amount: number;
  amount_status: string;
  overall_status: string;
  return_code: number;
}

export interface FinancialControlTotalModel {
  bank_record_count: number;
  bank_total_amount: number;
  merch_record_count: number;
  merch_total_amount: number;
  matched_count: number;
  matched_amount: number;
  amount_mismatch_count: number;
  amount_mismatch_amount: number;
  status_mismatch_count: number;
  missing_bank_count: number;
  missing_bank_amount: number;
  missing_merch_count: number;
  missing_merch_amount: number;
  total_exception_count: number;
  total_exception_amount: number;
  overall_amount_difference: number;
  control_status: string;
  accounting_equation_balanced: boolean;
}

export interface BatchInfo {
  batch_id: string;
  mode: ExecutionMode;
  status: BatchStatus;
  created_at: string;
  completed_at?: string;
  summary?: ReportSummary;
  control_totals?: ControlTotalResult;
  financial_controls?: FinancialControlTotalModel;
  return_code: number;
}

export type TriageStatus = 'UNASSIGNED' | 'IN_REVIEW' | 'RESOLVED' | 'REJECTED';

export type ResolutionCode =
  | 'RESOLVED_VALID_TRANSACTION'
  | 'RESOLVED_DATA_CORRECTION'
  | 'RESOLVED_DUPLICATE_CONFIRMED'
  | 'RESOLVED_SOURCE_DELAY'
  | 'REJECTED_FALSE_POSITIVE'
  | 'REJECTED_INVALID_CASE';

export interface InvestigationNote {
  note_id: string;
  exception_id: string;
  author: string;
  timestamp: string;
  note_text: string;
}

export interface ExceptionModel {
  exception_id: string;
  batch_id: string;
  transaction_id: string;
  reason_code: string;
  reason_description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  reconciliation_status: string;
  bank_amount: number;
  merchant_amount: number;
  amount_difference: number;
  bank_status: string;
  merchant_status: string;
  triage_status: TriageStatus;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  resolution_code?: ResolutionCode | null;
  resolution_notes?: string | null;
  notes: InvestigationNote[];
}

export interface ExceptionSummaryModel {
  total_exceptions: number;
  unassigned_count: number;
  in_review_count: number;
  resolved_count: number;
  rejected_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_financial_exposure: number;
  open_financial_exposure: number;
}

export interface AuditEventItem {
  event_id: string;
  exception_id: string;
  batch_id: string;
  event_type: string;
  actor: string;
  role?: string;
  timestamp: string;
  old_status?: string | null;
  new_status?: string | null;
  details: string;
}

export interface ExceptionItem {
  exception_id?: string;
  batch_id: string;
  trxn_id: string;
  transaction_id?: string;
  exception_code: string;
  reason_code?: string;
  exception_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  bank_amount: number;
  merch_amount: number;
  amount_difference: number;
  bank_status: string;
  merch_status: string;
  processing_date: string;
  triage_status?: TriageStatus;
  assigned_to?: string | null;
  notes?: InvestigationNote[];
}

export interface TransactionItem {
  trxn_id: string;
  acct_no: string;
  amount: number;
  trxn_date: string;
  trxn_status: string;
  bank_status: string;
  merch_status: string;
  recon_result: string;
  exception_code: string;
}

export interface TransactionDetail {
  transaction_id: string;
  acct_no: string;
  trxn_date: string;
  trxn_time: string;
  amount: number;
  trxn_type: string;
  merch_id: string;
  ref_no: string;
  bank_record: { acct_no: string; amt: number; status: string; key_pos: string };
  merch_record: { merch_id: string; amt: number; status: string; key_pos: string };
  recon_result: string;
  reason_code: string;
  severity: string;
  amount_difference: number;
}

export interface AuditLogItem {
  timestamp: string;
  step: string;
  name: string;
  status: string;
  rc: number;
}

// Feature A Types
export interface ControlCheckpointModel {
  id: string;
  batch_id: string;
  stage_name: string;
  timestamp: string;
  input_record_count: number;
  output_record_count: number;
  input_amount_total: number;
  output_amount_total: number;
  duplicate_count: number;
  matched_count: number;
  mismatch_count: number;
  missing_count: number;
  return_code: number;
  control_status: string;
  checksum?: string;
  lineage_ref?: string;
  recovery_status: string;
  recovery_attempt: number;
  created_at: string;
  completed_at?: string;
  error_reason?: string;
}

export interface RecoveryEventModel {
  id: string;
  batch_id: string;
  stage_name: string;
  event_type: string;
  attempt_number: number;
  status: string;
  message: string;
  created_at: string;
}

export interface RecoveryResponse {
  batch_id: string;
  recovered_stage: string;
  recovery_status: string;
  attempts: number;
  message: string;
  checkpoints: ControlCheckpointModel[];
}

// Feature B Types
export interface LineageEventModel {
  id: string;
  batch_id: string;
  transaction_id: string;
  event_type: string;
  stage_name: string;
  source_system: string;
  record_reference?: string;
  reason_code?: string;
  previous_state?: string;
  new_state?: string;
  actor: string;
  actor_role: string;
  metadata_json?: string;
  timestamp: string;
}

export interface TransactionLineageResponse {
  transaction_id: string;
  batch_id: string;
  events: LineageEventModel[];
}

export interface DecisionExplanationModel {
  transaction_id: string;
  batch_id: string;
  reason_code: string;
  reason_description: string;
  bank_amount: number;
  merchant_amount: number;
  amount_difference: number;
  bank_status: string;
  merchant_status: string;
  decision: string;
}

// Feature C Types
export interface FeatureScoresModel {
  amount_similarity: number;
  date_similarity: number;
  merchant_similarity: number;
  reference_similarity: number;
  account_similarity: number;
  status_similarity: number;
}

export interface IntelligentMatchResultModel {
  id: string;
  batch_id: string;
  bank_transaction_id: string;
  candidate_transaction_id: string;
  confidence_score: number;
  decision: string;
  confidence_classification: string;
  feature_scores: FeatureScoresModel;
  model_version: string;
  created_at: string;
}

export interface MatchAnalysisResponse {
  transaction_id: string;
  deterministic_result: string;
  intelligent_analysis?: IntelligentMatchResultModel | null;
}

// Authentication & RBAC Types
export type UserRole = 'USER' | 'SUPERVISOR' | 'ANALYST';

export interface UserProfile {
  id: string;
  username: string;
  role: UserRole;
  full_name?: string;
  is_active?: boolean;
}

export interface LoginResponse {
  user: UserProfile;
  token: string;
  session_token?: string;
  token_type: string;
  expires_at: string;
}



