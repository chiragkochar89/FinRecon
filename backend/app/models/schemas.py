from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class BatchStatusEnum(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    RECONCILING = "RECONCILING"
    VALIDATING_TOTALS = "VALIDATING_TOTALS"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_EXCEPTIONS = "COMPLETED_WITH_EXCEPTIONS"
    FAILED = "FAILED"

class ExecutionModeEnum(str, Enum):
    LOCAL_DEMO = "LOCAL_DEMO"
    REAL_MAINFRAME = "REAL_MAINFRAME"

class SeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ReasonCodeEnum(str, Enum):
    RCN_000 = "RCN-000"  # MATCHED
    RCN_101 = "RCN-101"  # AMOUNT_MISMATCH
    RCN_102 = "RCN-102"  # STATUS_MISMATCH
    RCN_103 = "RCN-103"  # MISSING_IN_BANK
    RCN_104 = "RCN-104"  # MISSING_IN_MERCHANT
    RCN_105 = "RCN-105"  # DUPLICATE_TRANSACTION
    RCN_106 = "RCN-106"  # INVALID_TRANSACTION
    RCN_107 = "RCN-107"  # INVALID_ACCOUNT
    RCN_108 = "RCN-108"  # RECORD_FORMAT_ERROR

class HealthCheckResponse(BaseModel):
    status: str
    mode: ExecutionModeEnum
    service: str
    version: str

class FileValidationRequest(BaseModel):
    bank_file_content: Optional[str] = None
    merch_file_content: Optional[str] = None
    audit_file_content: Optional[str] = None

class FileValidationResponse(BaseModel):
    valid: bool
    bank_record_count: int
    merch_record_count: int
    audit_record_count: int
    validation_messages: List[str]

class BatchCreateRequest(BaseModel):
    batch_description: Optional[str] = "Standard Daily Financial Reconciliation Batch"
    batch_id: Optional[str] = None

class TransactionItem(BaseModel):
    trxn_id: str
    acct_no: str
    trxn_date: str
    trxn_time: str
    amount: float
    curr_code: str
    trxn_type: str
    trxn_stat: str
    merch_id: str
    ref_no: str
    recon_status: str
    reason_code: ReasonCodeEnum
    severity: SeverityEnum

class ExceptionItem(BaseModel):
    batch_id: str
    trxn_id: str
    exception_code: ReasonCodeEnum
    exception_type: str
    severity: SeverityEnum
    bank_amount: float
    merch_amount: float
    amount_difference: float
    bank_status: str
    merch_status: str
    recon_result: str
    processing_date: str

class ControlTotalResult(BaseModel):
    input_record_count: int
    output_record_count: int
    count_status: str
    input_total_amount: float
    output_total_amount: float
    amount_status: str
    overall_status: str
    return_code: int

class FinancialControlTotalModel(BaseModel):
    bank_record_count: int
    bank_total_amount: float
    merch_record_count: int
    merch_total_amount: float
    matched_count: int
    matched_amount: float
    amount_mismatch_count: int
    amount_mismatch_amount: float
    status_mismatch_count: int
    missing_bank_count: int
    missing_bank_amount: float
    missing_merch_count: int
    missing_merch_amount: float
    total_exception_count: int
    total_exception_amount: float
    overall_amount_difference: float
    control_status: str
    accounting_equation_balanced: bool

class TriageStatusEnum(str, Enum):
    UNASSIGNED = "UNASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

class ResolutionCodeEnum(str, Enum):
    RESOLVED_VALID_TRANSACTION = "RESOLVED_VALID_TRANSACTION"
    RESOLVED_DATA_CORRECTION = "RESOLVED_DATA_CORRECTION"
    RESOLVED_DUPLICATE_CONFIRMED = "RESOLVED_DUPLICATE_CONFIRMED"
    RESOLVED_SOURCE_DELAY = "RESOLVED_SOURCE_DELAY"
    REJECTED_FALSE_POSITIVE = "REJECTED_FALSE_POSITIVE"
    REJECTED_INVALID_CASE = "REJECTED_INVALID_CASE"

class InvestigationNote(BaseModel):
    note_id: str
    exception_id: str
    author: str
    timestamp: str
    note_text: str

class ExceptionModel(BaseModel):
    exception_id: str
    batch_id: str
    transaction_id: str
    reason_code: ReasonCodeEnum
    reason_description: str
    severity: SeverityEnum
    reconciliation_status: str
    bank_amount: float
    merchant_amount: float
    amount_difference: float
    bank_status: str
    merchant_status: str
    triage_status: TriageStatusEnum = TriageStatusEnum.UNASSIGNED
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    resolution_code: Optional[ResolutionCodeEnum] = None
    resolution_notes: Optional[str] = None
    notes: List[InvestigationNote] = Field(default_factory=list)

class ExceptionSummaryModel(BaseModel):
    total_exceptions: int
    unassigned_count: int
    in_review_count: int
    resolved_count: int
    rejected_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_financial_exposure: float
    open_financial_exposure: float

class AssignExceptionRequest(BaseModel):
    assignee: str
    actor: Optional[str] = "OPERATOR"

class AddNoteRequest(BaseModel):
    author: Optional[str] = "ANALYST_01"
    note_text: str

class UpdateStatusRequest(BaseModel):
    target_status: TriageStatusEnum
    resolution_code: Optional[ResolutionCodeEnum] = None
    resolution_notes: Optional[str] = None
    actor: Optional[str] = "OPERATOR"

class UserRoleEnum(str, Enum):
    USER = "USER"
    ANALYST = "ANALYST"          # Backward-compatibility alias for USER
    SUPERVISOR = "SUPERVISOR"

class UserProfile(BaseModel):
    id: str
    username: str
    role: str
    full_name: Optional[str] = None
    is_active: bool = True

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user: UserProfile
    token: str
    session_token: Optional[str] = None
    token_type: str = "bearer"
    expires_at: str


class UserContextModel(BaseModel):
    username: str
    role: UserRoleEnum
    user_id: Optional[str] = None
    mode: ExecutionModeEnum = ExecutionModeEnum.LOCAL_DEMO

class AuditEventModel(BaseModel):
    event_id: str
    exception_id: str
    batch_id: str
    actor: str
    role: str = "ANALYST"
    event_type: str
    timestamp: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    details: str

class ReportSummary(BaseModel):
    batch_id: str
    process_date: str
    total_bank_records: int
    total_merch_records: int
    matched_count: int
    amount_mismatch_count: int
    status_mismatch_count: int
    missing_bank_count: int
    missing_merch_count: int
    total_exceptions: int
    matched_amount: float
    total_discrepancy_amount: float
    final_status: str
    report_text: str

class BatchResponse(BaseModel):
    batch_id: str
    mode: ExecutionModeEnum
    status: BatchStatusEnum
    created_at: str
    completed_at: Optional[str] = None
    summary: Optional[ReportSummary] = None
    control_totals: Optional[ControlTotalResult] = None
    financial_controls: Optional[FinancialControlTotalModel] = None
    return_code: int

# ============================================================
# FEATURE A: SELF-HEALING FINANCIAL CONTROL & BATCH RECOVERY
# ============================================================

class ControlCheckpointModel(BaseModel):
    id: str
    batch_id: str
    stage_name: str
    timestamp: str
    input_record_count: int
    output_record_count: int
    input_amount_total: float
    output_amount_total: float
    duplicate_count: int = 0
    matched_count: int = 0
    mismatch_count: int = 0
    missing_count: int = 0
    return_code: int = 0
    control_status: str  # PASSED, WARNING, FAILED_CONTROL, RECOVERED
    checksum: Optional[str] = None
    lineage_ref: Optional[str] = None
    recovery_status: str  # NORMAL, CONTROL_FAILURE, DIAGNOSING, RECOVERY_ATTEMPT, REVALIDATING, RECOVERED, RECOVERY_FAILED, ESCALATED
    recovery_attempt: int = 0
    created_at: str
    completed_at: Optional[str] = None
    error_reason: Optional[str] = None

class RecoveryEventModel(BaseModel):
    id: str
    batch_id: str
    stage_name: str
    event_type: str
    attempt_number: int
    status: str
    message: str
    created_at: str

class SimulateFailureRequest(BaseModel):
    batch_id: Optional[str] = "FINREC-20260922-001"
    stage: str = "DFSORT_DEDUP"
    failure_type: str = "AMOUNT_CONTROL_MISMATCH"

class RecoveryResponse(BaseModel):
    batch_id: str
    recovered_stage: str
    recovery_status: str
    attempts: int
    message: str
    checkpoints: List[ControlCheckpointModel]

# ============================================================
# FEATURE B: TRANSACTION LINEAGE GRAPH
# ============================================================

class LineageEventModel(BaseModel):
    id: str
    batch_id: str
    transaction_id: str
    event_type: str
    stage_name: str
    source_system: str
    record_reference: Optional[str] = None
    reason_code: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    actor: str
    actor_role: str
    metadata_json: Optional[str] = None
    timestamp: str

class TransactionLineageResponse(BaseModel):
    transaction_id: str
    batch_id: str
    events: List[LineageEventModel]

class DecisionExplanationModel(BaseModel):
    transaction_id: str
    batch_id: str
    reason_code: str
    reason_description: str
    bank_amount: float
    merchant_amount: float
    amount_difference: float
    bank_status: str
    merchant_status: str
    decision: str

# ============================================================
# FEATURE C: INTELLIGENT HYBRID RECONCILIATION
# ============================================================

class IntelligentMatchRequest(BaseModel):
    bank_transaction_id: str
    batch_id: Optional[str] = "FINREC-20260922-001"

class FeatureScoresModel(BaseModel):
    amount_similarity: float
    date_similarity: float
    merchant_similarity: float
    reference_similarity: float
    account_similarity: float
    status_similarity: float

class IntelligentMatchResultModel(BaseModel):
    id: str
    batch_id: str
    bank_transaction_id: str
    candidate_transaction_id: str
    confidence_score: float
    decision: str  # AUTO_MATCH, REVIEW, EXCEPTION
    confidence_classification: str # HIGH, MEDIUM, LOW
    feature_scores: FeatureScoresModel
    model_version: str
    created_at: str

class MatchAnalysisResponse(BaseModel):
    transaction_id: str
    deterministic_result: str
    intelligent_analysis: Optional[IntelligentMatchResultModel] = None


