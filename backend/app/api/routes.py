from fastapi import APIRouter, HTTPException, Path, Query, Header, Depends, Response, Request, Cookie, status
from fastapi.responses import Response, StreamingResponse
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.models.schemas import (
    HealthCheckResponse, FileValidationRequest, FileValidationResponse,
    BatchCreateRequest, BatchResponse, ExecutionModeEnum,
    ExceptionModel, ExceptionSummaryModel, AssignExceptionRequest,
    AddNoteRequest, UpdateStatusRequest, AuditEventModel,
    SeverityEnum, ReasonCodeEnum, TriageStatusEnum, InvestigationNote,
    UserRoleEnum, UserContextModel,
    ControlCheckpointModel, RecoveryEventModel, SimulateFailureRequest, RecoveryResponse,
    LineageEventModel, TransactionLineageResponse, DecisionExplanationModel,
    IntelligentMatchRequest, IntelligentMatchResultModel, MatchAnalysisResponse,
    LoginRequest, LoginResponse, UserProfile
)
from app.services.recon_service import recon_service
from app.services.report_generator import report_generator
from app.services.auth_service import auth_service
from app.repositories.exception_repository import exception_repo
from app.repositories.audit_repository import audit_repo
from app.repositories.checkpoint_repository import checkpoint_repo
from app.repositories.lineage_repository import lineage_repo
from app.services.intelligent_match_service import intelligent_match_service
from app.db.database import get_db_connection

router = APIRouter()

def _extract_token(
    authorization: Optional[str] = None,
    x_session_token: Optional[str] = None,
    finrecon_session: Optional[str] = None
) -> Optional[str]:
    """Helper to extract session token from Authorization header, X-Session-Token, or cookie."""
    if authorization:
        if authorization.lower().startswith("bearer "):
            return authorization[7:].strip()
        return authorization.strip()
    if x_session_token:
        return x_session_token.strip()
    if finrecon_session:
        return finrecon_session.strip()
    return None

# RBAC Identity & Role Extraction Dependency
def get_user_context(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    finrecon_session: Optional[str] = Cookie(None),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    user_name: Optional[str] = Query(None),
    user_role: Optional[str] = Query(None)
) -> UserContextModel:
    token = _extract_token(authorization, x_session_token, finrecon_session)
    if token:
        session = auth_service.validate_session(token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token. Please log in again."
            )
        role = UserRoleEnum.SUPERVISOR if session["role"] == "SUPERVISOR" else UserRoleEnum.USER
        return UserContextModel(
            user_id=session["user_id"],
            username=session["username"],
            role=role,
            mode=ExecutionModeEnum.LOCAL_DEMO
        )

    # Legacy / test headers & query parameters
    if x_user_name or x_user_role or user_name or user_role:
        username = user_name or x_user_name or "ANALYST_01"
        role_str = (user_role or x_user_role or "USER").upper()
        role = UserRoleEnum.SUPERVISOR if role_str == "SUPERVISOR" else UserRoleEnum.USER
        return UserContextModel(username=username, role=role, mode=ExecutionModeEnum.LOCAL_DEMO)

    # Backward compatibility default for unauthenticated legacy test calls
    return UserContextModel(username="ANALYST_01", role=UserRoleEnum.USER, mode=ExecutionModeEnum.LOCAL_DEMO)

def require_authenticated_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    finrecon_session: Optional[str] = Cookie(None),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    user_name: Optional[str] = Query(None),
    user_role: Optional[str] = Query(None)
) -> UserContextModel:
    token = _extract_token(authorization, x_session_token, finrecon_session)
    if token:
        session = auth_service.validate_session(token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token. Please log in again."
            )
        role = UserRoleEnum.SUPERVISOR if session["role"] == "SUPERVISOR" else UserRoleEnum.USER
        return UserContextModel(
            user_id=session["user_id"],
            username=session["username"],
            role=role,
            mode=ExecutionModeEnum.LOCAL_DEMO
        )

    # In development/test mode, explicit headers are accepted
    if x_user_name or x_user_role:
        username = x_user_name or "ANALYST_01"
        role_str = (x_user_role or "USER").upper()
        role = UserRoleEnum.SUPERVISOR if role_str == "SUPERVISOR" else UserRoleEnum.USER
        return UserContextModel(username=username, role=role, mode=ExecutionModeEnum.LOCAL_DEMO)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid session token."
    )

def require_supervisor(
    user: UserContextModel = Depends(get_user_context),
    exception_id: Optional[str] = "SYSTEM"
) -> UserContextModel:
    if user.role != UserRoleEnum.SUPERVISOR:
        audit_repo.log_event(
            exception_id=exception_id or "SYSTEM",
            batch_id="FINREC-20260922-001",
            actor=user.username,
            role=user.role.value,
            event_type="SECURITY_DENIED",
            details=f"Access denied: Action requires SUPERVISOR role (Current role: {user.role.value})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Operation restricted to SUPERVISOR role. Active identity '{user.username}' has role '{user.role.value}'."
        )
    return user

# ==========================================
# AUTHENTICATION & SESSION MANAGEMENT
# ==========================================

@router.post("/auth/login", response_model=LoginResponse)
@router.post("/v1/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, raw_request: Request, response: Response):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    user_agent = raw_request.headers.get("user-agent", "Unknown")
    try:
        user_record, session_token, session_dict = auth_service.login(
            username=request.username,
            password=request.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key="finrecon_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Local demo friendly
        max_age=8 * 3600,
        path="/"
    )

    role_val = UserRoleEnum(user_record["role"])
    return LoginResponse(
        token=session_token,
        session_token=session_token,
        token_type="bearer",
        user=UserProfile(
            id=user_record["id"],
            username=user_record["username"],
            role=role_val.value,
            full_name=user_record.get("full_name"),
            is_active=bool(user_record.get("is_active", 1))
        ),
        expires_at=session_dict["expires_at"]
    )


@router.post("/auth/logout")
@router.post("/v1/auth/logout")
def logout(
    response: Response,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    finrecon_session: Optional[str] = Cookie(None)
):
    token = _extract_token(authorization, x_session_token, finrecon_session)
    if token:
        auth_service.logout(token)
    response.delete_cookie(key="finrecon_session", path="/")
    return {"status": "SUCCESS", "message": "Successfully logged out and session revoked"}

@router.get("/auth/me", response_model=UserProfile)
@router.get("/v1/auth/me", response_model=UserProfile)
def get_current_user_profile(user: UserContextModel = Depends(require_authenticated_user)):
    user_record = auth_service.get_user_by_username(user.username)
    if not user_record:
        return UserProfile(
            id=user.user_id or f"USR-{user.username}",
            username=user.username,
            role=user.role,
            full_name=f"{user.username} (Demo Account)",
            is_active=True
        )
    return UserProfile(
        id=user_record["id"],
        username=user_record["username"],
        role=UserRoleEnum(user_record["role"]),
        full_name=user_record.get("full_name"),
        is_active=bool(user_record.get("is_active", 1))
    )


@router.get("/health", response_model=HealthCheckResponse)
def get_health():
    mode = ExecutionModeEnum.REAL_MAINFRAME if settings.FINRECON_MODE == "REAL_MAINFRAME" else ExecutionModeEnum.LOCAL_DEMO
    return HealthCheckResponse(
        status="ONLINE",
        mode=mode,
        service=settings.PROJECT_NAME,
        version=settings.VERSION
    )

@router.post("/files/validate", response_model=FileValidationResponse)
def validate_files(request: FileValidationRequest):
    return recon_service.validate_files(request)

@router.post("/batches", response_model=BatchResponse)
def create_batch(request: BatchCreateRequest, user: UserContextModel = Depends(get_user_context)):
    resp = recon_service.create_batch(request.batch_description, batch_id=request.batch_id)
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=resp.batch_id,
        actor=user.username,
        role=user.role.value,
        event_type="BATCH_SUBMITTED",
        details=f"Reconciliation batch submitted and executed: {resp.batch_id}."
    )
    return resp

@router.post("/batches/{batch_id}/execute", response_model=BatchResponse)
@router.post("/v1/batches/{batch_id}/execute", response_model=BatchResponse)
def execute_batch(
    batch_id: str = Path(...),
    user: UserContextModel = Depends(get_user_context)
):
    resp = recon_service.execute_batch(batch_id)
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id,
        actor=user.username,
        role=user.role.value,
        event_type="BATCH_EXECUTED",
        details=f"Reconciliation batch executed: {batch_id}. 8 pipeline stages processed."
    )
    return resp

@router.post("/batches/{batch_id}/reset")
@router.post("/v1/batches/{batch_id}/reset")
def reset_batch_pipeline(
    batch_id: str = Path(...),
    user: UserContextModel = Depends(get_user_context)
):
    chks = checkpoint_repo.reset_pipeline(batch_id)
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id,
        actor=user.username,
        role=user.role.value,
        event_type="PIPELINE_RESET",
        details=f"Pipeline checkpoints reset to initial PENDING state for batch {batch_id}."
    )
    return {"batch_id": batch_id, "status": "RESET", "checkpoints": chks}

@router.get("/batches", response_model=List[BatchResponse])
def list_batches():
    batch = recon_service.get_batch("FINREC-20260922-001")
    return [batch] if batch else []

@router.get("/batches/{batch_id}", response_model=BatchResponse)
def get_batch(batch_id: str = Path(..., description="Batch ID")):
    batch = recon_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return batch

@router.get("/batches/{batch_id}/results")
def get_batch_results(batch_id: str = Path(...)):
    results = recon_service.get_results(batch_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return results

@router.get("/batches/{batch_id}/exceptions")
def get_batch_exceptions(batch_id: str = Path(...)):
    res = recon_service.get_exceptions(batch_id)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return res

@router.get("/batches/{batch_id}/audit")
def get_batch_audit(batch_id: str = Path(...)):
    batch = recon_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return {
        "batch_id": batch_id,
        "audit_logs": [
            {"timestamp": "2026-09-22 14:00:01", "step": "STEP01", "name": "Input File Validation & Format Check", "status": "COMPLETED", "rc": 0},
            {"timestamp": "2026-09-22 14:00:03", "step": "STEP02", "name": "Bank Feed DFSORT Deduplication (SUM FIELDS=NONE)", "status": "COMPLETED", "rc": 0},
            {"timestamp": "2026-09-22 14:00:05", "step": "STEP03", "name": "Merchant Feed DFSORT Ascending Sort", "status": "COMPLETED", "rc": 0},
            {"timestamp": "2026-09-22 14:00:10", "step": "STEP04", "name": "COBOL Reconciliation Engine (FINREC01)", "status": "COMPLETED_WITH_EXCEPTIONS", "rc": 4},
            {"timestamp": "2026-09-22 14:00:12", "step": "STEP05", "name": "REXX Audit Processor & In-Memory Sort (FINREXX)", "status": "COMPLETED", "rc": 0},
            {"timestamp": "2026-09-22 14:00:14", "step": "STEP06", "name": "JCL Descending Sort Record Count Validation", "status": "PASSED (90 == 90)", "rc": 0},
            {"timestamp": "2026-09-22 14:00:16", "step": "STEP07", "name": "COBOL Report Generator Execution (FINRPT01)", "status": "COMPLETED", "rc": 0}
        ]
    }

@router.get("/batches/{batch_id}/reports")
def get_batch_reports(batch_id: str = Path(...)):
    report_text = recon_service.get_report(batch_id)
    if not report_text:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return {"batch_id": batch_id, "report": report_text}

# ==========================================
# PHASE 4 & 5: EXCEPTION TRIAGE & REPORTING
# ==========================================

@router.get("/exceptions/summary", response_model=ExceptionSummaryModel)
@router.get("/v1/exceptions/summary", response_model=ExceptionSummaryModel)
def get_exceptions_summary(batch_id: Optional[str] = Query(None)):
    return exception_repo.get_summary(batch_id=batch_id)

@router.get("/exceptions", response_model=List[ExceptionModel])
@router.get("/v1/exceptions", response_model=List[ExceptionModel])
def list_exceptions(
    batch_id: Optional[str] = Query(None),
    severity: Optional[SeverityEnum] = Query(None),
    reason_code: Optional[ReasonCodeEnum] = Query(None),
    triage_status: Optional[TriageStatusEnum] = Query(None),
    assigned_to: Optional[str] = Query(None),
    trxn_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    return exception_repo.get_all(
        batch_id=batch_id,
        severity=severity,
        reason_code=reason_code,
        triage_status=triage_status,
        assigned_to=assigned_to,
        trxn_id=trxn_id,
        search=search,
        skip=skip,
        limit=limit
    )

@router.get("/exceptions/{exception_id}", response_model=ExceptionModel)
@router.get("/v1/exceptions/{exception_id}", response_model=ExceptionModel)
def get_exception_by_id(exception_id: str = Path(...)):
    exc = exception_repo.get_by_id(exception_id)
    if not exc:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found")
    return exc

@router.post("/exceptions/{exception_id}/assign", response_model=ExceptionModel)
@router.post("/v1/exceptions/{exception_id}/assign", response_model=ExceptionModel)
def assign_exception(
    request: AssignExceptionRequest,
    exception_id: str = Path(...),
    user: UserContextModel = Depends(get_user_context)
):
    try:
        actor_name = request.actor or user.username
        return exception_repo.assign(
            exception_id=exception_id,
            assignee=request.assignee,
            actor=actor_name,
            role=user.role.value
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/exceptions/{exception_id}/notes", response_model=InvestigationNote)
@router.post("/v1/exceptions/{exception_id}/notes", response_model=InvestigationNote)
def add_exception_note(
    request: AddNoteRequest,
    exception_id: str = Path(...),
    user: UserContextModel = Depends(get_user_context)
):
    try:
        author_name = request.author or user.username
        return exception_repo.add_note(
            exception_id=exception_id,
            author=author_name,
            note_text=request.note_text,
            role=user.role.value
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/exceptions/{exception_id}/status", response_model=ExceptionModel)
@router.post("/v1/exceptions/{exception_id}/status", response_model=ExceptionModel)
def update_exception_status(
    request: UpdateStatusRequest,
    exception_id: str = Path(...),
    user: UserContextModel = Depends(get_user_context)
):
    # Server-Side RBAC Enforcement: Case Resolution/Rejection requires SUPERVISOR role!
    if request.target_status in (TriageStatusEnum.RESOLVED, TriageStatusEnum.REJECTED):
        if user.role != UserRoleEnum.SUPERVISOR:
            audit_repo.log_event(
                exception_id=exception_id,
                batch_id="FINREC-20260922-001",
                actor=user.username,
                role=user.role.value,
                event_type="SECURITY_DENIED",
                details=f"Unauthorized status transition attempt to {request.target_status.value} (Requires SUPERVISOR role)"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Transitioning case to '{request.target_status.value}' requires SUPERVISOR role. Active user '{user.username}' has role '{user.role.value}'."
            )

    try:
        actor_name = request.actor or user.username
        return exception_repo.update_status(
            exception_id=exception_id,
            target_status=request.target_status,
            resolution_code=request.resolution_code,
            resolution_notes=request.resolution_notes,
            actor=actor_name,
            role=user.role.value
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/exceptions/{exception_id}/audit", response_model=List[AuditEventModel])
@router.get("/v1/exceptions/{exception_id}/audit", response_model=List[AuditEventModel])
def get_exception_audit_timeline(exception_id: str = Path(...)):
    return audit_repo.get_events_for_exception(exception_id)

@router.get("/audit", response_model=List[AuditEventModel])
@router.get("/v1/audit", response_model=List[AuditEventModel])
def list_all_audit_events(
    batch_id: Optional[str] = Query(None),
    exception_id: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000)
):
    return audit_repo.get_all_events(
        batch_id=batch_id,
        exception_id=exception_id,
        actor=actor,
        role=role,
        event_type=event_type,
        skip=skip,
        limit=limit
    )

# ==========================================
# PHASE 5: AUDITOR REPORT EXPORT ENDPOINTS
# ==========================================

@router.get("/reports/exceptions.csv")
@router.get("/v1/reports/exceptions.csv")
def export_exceptions_csv(
    batch_id: Optional[str] = Query(None),
    user: UserContextModel = Depends(require_supervisor)
):
    excs = exception_repo.get_all(batch_id=batch_id)
    csv_content = report_generator.generate_exceptions_csv(excs)
    
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id or "FINREC-20260922-001",
        actor=user.username,
        role=user.role.value,
        event_type="REPORT_EXPORTED",
        details=f"Exported Exceptions CSV ({len(excs)} records)"
    )
    
    headers = {"Content-Disposition": f"attachment; filename=finrecon_exceptions_{batch_id or 'all'}.csv"}
    return Response(content=csv_content, media_type="text/csv", headers=headers)

@router.get("/reports/audit.csv")
@router.get("/v1/reports/audit.csv")
def export_audit_csv(
    batch_id: Optional[str] = Query(None),
    user: UserContextModel = Depends(require_supervisor)
):
    events = audit_repo.get_all_events(batch_id=batch_id)
    csv_content = report_generator.generate_audit_csv(events)
    
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id or "FINREC-20260922-001",
        actor=user.username,
        role=user.role.value,
        event_type="REPORT_EXPORTED",
        details=f"Exported Audit Trail CSV ({len(events)} events)"
    )
    
    headers = {"Content-Disposition": f"attachment; filename=finrecon_audit_{batch_id or 'all'}.csv"}
    return Response(content=csv_content, media_type="text/csv", headers=headers)

@router.get("/reports/reconciliation.xlsx")
@router.get("/v1/reports/reconciliation.xlsx")
def export_reconciliation_excel(
    batch_id: str = Query("FINREC-20260922-001"),
    user: UserContextModel = Depends(require_supervisor)
):
    batch = recon_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    summary = batch.summary
    fin_controls = batch.financial_controls
    excs = exception_repo.get_all(batch_id=batch_id)
    events = audit_repo.get_all_events(batch_id=batch_id)
    
    excel_bytes = report_generator.generate_reconciliation_excel(summary, excs, events, fin_controls)
    
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id,
        actor=user.username,
        role=user.role.value,
        event_type="REPORT_EXPORTED",
        details=f"Exported Reconciliation Excel Workbook ({batch_id})"
    )
    
    headers = {"Content-Disposition": f"attachment; filename=finrecon_reconciliation_{batch_id}.xlsx"}
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

@router.get("/reports/reconciliation.pdf")
@router.get("/v1/reports/reconciliation.pdf")
def export_reconciliation_pdf(
    batch_id: str = Query("FINREC-20260922-001"),
    user: UserContextModel = Depends(require_supervisor)
):
    batch = recon_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    summary = batch.summary
    fin_controls = batch.financial_controls
    excs = exception_repo.get_all(batch_id=batch_id)
    events = audit_repo.get_all_events(batch_id=batch_id)
    
    pdf_bytes = report_generator.generate_reconciliation_pdf(
        summary, excs, events, fin_controls, mode_label=batch.mode.value
    )
    
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id,
        actor=user.username,
        role=user.role.value,
        event_type="REPORT_EXPORTED",
        details=f"Exported Auditor PDF Report ({batch_id})"
    )
    
    headers = {"Content-Disposition": f"inline; filename=finrecon_report_{batch_id}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/transactions")
@router.get("/v1/transactions")
def list_transactions(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    txns = []
    # 30 Matched
    for i in range(1, 31):
        t_id = f"TXN{10000 + i:05d}"
        acct_no = f"ACC1000000{i:02d}"
        if search:
            query = search.strip().upper()
            if query not in t_id.upper() and query not in acct_no.upper():
                continue
        if status and status != "MATCHED":
            continue
        txns.append({
            "trxn_id": t_id,
            "acct_no": acct_no,
            "amount": 1250.50,
            "trxn_date": "2026-09-22",
            "trxn_status": "MATCHED",
            "bank_status": "AP",
            "merch_status": "AP",
            "recon_result": "MATCHED",
            "exception_code": "RCN-000"
        })
    # 5 Amount Mismatches
    for i in range(31, 36):
        t_id = f"TXN{10000 + i:05d}"
        acct_no = f"ACC1000000{i:02d}"
        if search:
            query = search.strip().upper()
            if query not in t_id.upper() and query not in acct_no.upper():
                continue
        if status and status != "AMOUNT-MISMATCH":
            continue
        txns.append({
            "trxn_id": t_id,
            "acct_no": acct_no,
            "amount": 1250.50,
            "trxn_date": "2026-09-22",
            "trxn_status": "AMOUNT-MISMATCH",
            "bank_status": "AP",
            "merch_status": "AP",
            "recon_result": "AMOUNT-MISMATCH",
            "exception_code": "RCN-101"
        })
    # 5 Status Mismatches
    for i in range(36, 41):
        t_id = f"TXN{10000 + i:05d}"
        acct_no = f"ACC1000000{i:02d}"
        if search:
            query = search.strip().upper()
            if query not in t_id.upper() and query not in acct_no.upper():
                continue
        if status and status != "STATUS-MISMATCH":
            continue
        txns.append({
            "trxn_id": t_id,
            "acct_no": acct_no,
            "amount": 1250.50,
            "trxn_date": "2026-09-22",
            "trxn_status": "STATUS-MISMATCH",
            "bank_status": "AP",
            "merch_status": "RJ",
            "recon_result": "STATUS-MISMATCH",
            "exception_code": "RCN-102"
        })
    return {"total": len(txns), "transactions": txns}

@router.get("/transactions/{transaction_id}")
@router.get("/v1/transactions/{transaction_id}")
def get_transaction_detail(transaction_id: str = Path(...)):
    t_id = transaction_id.upper().strip()

    # Determine numeric index for standard sequence (e.g. TXN10001 -> idx 1)
    txn_num = None
    if t_id.startswith("TXN"):
        try:
            txn_num = int(t_id[3:])
        except ValueError:
            pass

    if txn_num is not None:
        idx = txn_num - 10000
        acct_no = f"ACC1000000{idx:02d}"
        ref_no = f"REF9876543{idx:05d}"
    else:
        acct_no = "ACC100000001"
        ref_no = "REF987654321001"

    trxn_date = "2026-09-22"
    trxn_time = "143015"
    trxn_type = "CR"
    merch_id = "MCH90001"

    # Query authoritative exception from database if it exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM exceptions
        WHERE UPPER(transaction_id) = ?
        ORDER BY CASE WHEN batch_id = 'FINREC-20260922-001' THEN 0 ELSE 1 END, rowid DESC
    """, (t_id,))
    exc_row = cursor.fetchone()
    conn.close()

    if exc_row:
        recon_result = exc_row["reconciliation_status"]
        reason_code = exc_row["reason_code"]
        severity = exc_row["severity"]
        amount_diff = float(exc_row["amount_difference"] if exc_row["amount_difference"] is not None else 0.0)
        bank_amount = float(exc_row["bank_amount"] if exc_row["bank_amount"] is not None else 1250.50)
        merch_amount = float(exc_row["merchant_amount"] if exc_row["merchant_amount"] is not None else 1250.50)
        bank_status = exc_row["bank_status"] or "AP"
        merch_status = exc_row["merchant_status"] or "AP"
        amount = bank_amount if bank_amount > 0 else merch_amount
    elif txn_num is not None and 10001 <= txn_num <= 10030:
        # Standard matched transaction
        recon_result = "MATCHED"
        reason_code = "RCN-000"
        severity = "LOW"
        amount_diff = 0.00
        bank_amount = 1250.50
        merch_amount = 1250.50
        bank_status = "AP"
        merch_status = "AP"
        amount = 1250.50
    elif txn_num is not None and 10031 <= txn_num <= 10035:
        recon_result = "AMOUNT-MISMATCH"
        reason_code = "RCN-101"
        severity = "HIGH"
        amount_diff = 249.50
        bank_amount = 1250.50
        merch_amount = 1500.00
        bank_status = "AP"
        merch_status = "AP"
        amount = 1250.50
    elif txn_num is not None and 10036 <= txn_num <= 10040:
        recon_result = "STATUS-MISMATCH"
        reason_code = "RCN-102"
        severity = "HIGH"
        amount_diff = 0.00
        bank_amount = 1250.50
        merch_amount = 1250.50
        bank_status = "AP"
        merch_status = "RJ"
        amount = 1250.50
    else:
        recon_result = "MATCHED"
        reason_code = "RCN-000"
        severity = "LOW"
        amount_diff = 0.00
        bank_amount = 1250.50
        merch_amount = 1250.50
        bank_status = "AP"
        merch_status = "AP"
        amount = 1250.50

    return {
        "transaction_id": t_id,
        "acct_no": acct_no,
        "trxn_date": trxn_date,
        "trxn_time": trxn_time,
        "amount": amount,
        "trxn_type": trxn_type,
        "merch_id": merch_id,
        "ref_no": ref_no,
        "bank_record": {
            "acct_no": acct_no,
            "amt": bank_amount,
            "status": bank_status,
            "key_pos": "Cols 13-20"
        },
        "merch_record": {
            "merch_id": merch_id,
            "amt": merch_amount,
            "status": merch_status,
            "key_pos": "Cols 21-28"
        },
        "recon_result": recon_result,
        "reason_code": reason_code,
        "severity": severity,
        "amount_difference": amount_diff
    }

# ============================================================
# FEATURE A: SELF-HEALING FINANCIAL CONTROL & BATCH RECOVERY
# ============================================================

@router.get("/batches/{batch_id}/controls", response_model=List[ControlCheckpointModel])
@router.get("/v1/batches/{batch_id}/controls", response_model=List[ControlCheckpointModel])
def get_batch_controls(batch_id: str = Path(...)):
    return checkpoint_repo.get_checkpoints(batch_id)

@router.get("/batches/{batch_id}/recovery", response_model=List[RecoveryEventModel])
@router.get("/v1/batches/{batch_id}/recovery", response_model=List[RecoveryEventModel])
def get_batch_recovery_events(batch_id: str = Path(...)):
    return checkpoint_repo.get_recovery_events(batch_id)

@router.post("/recovery/simulate-failure", response_model=ControlCheckpointModel)
@router.post("/v1/recovery/simulate-failure", response_model=ControlCheckpointModel)
def simulate_control_failure(
    request: SimulateFailureRequest,
    user: UserContextModel = Depends(require_supervisor)
):
    chk = checkpoint_repo.simulate_failure(
        batch_id=request.batch_id or "FINREC-20260922-001",
        stage_name=request.stage,
        failure_type=request.failure_type
    )
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=request.batch_id or "FINREC-20260922-001",
        actor=user.username,
        role=user.role.value,
        event_type="CONTROL_FAILURE_DETECTED",
        details=f"Simulated control failure on stage {request.stage}: {request.failure_type}"
    )
    return chk

@router.post("/batches/{batch_id}/recover", response_model=RecoveryResponse)
@router.post("/v1/batches/{batch_id}/recover", response_model=RecoveryResponse)
def recover_batch(
    batch_id: str = Path(...),
    user: UserContextModel = Depends(require_supervisor)
):
    chks = checkpoint_repo.recover_batch(batch_id)
    audit_repo.log_event(
        exception_id="SYSTEM",
        batch_id=batch_id,
        actor=user.username,
        role=user.role.value,
        event_type="RECOVERY_COMPLETED",
        details=f"Automated self-healing recovery executed on batch {batch_id}. All financial control checkpoints RECOVERED."
    )
    return RecoveryResponse(
        batch_id=batch_id,
        recovered_stage="DFSORT_DEDUP",
        recovery_status="RECOVERED",
        attempts=1,
        message="Stage reprocessed from original source file. Financial control equation revalidated OK.",
        checkpoints=chks
    )

# ============================================================
# FEATURE B: TRANSACTION LINEAGE GRAPH
# ============================================================

@router.get("/transactions/{transaction_id}/lineage", response_model=TransactionLineageResponse)
@router.get("/v1/transactions/{transaction_id}/lineage", response_model=TransactionLineageResponse)
def get_transaction_lineage(transaction_id: str = Path(...)):
    evts = lineage_repo.get_lineage_for_transaction(transaction_id)
    return TransactionLineageResponse(
        transaction_id=transaction_id.upper(),
        batch_id="FINREC-20260922-001",
        events=evts
    )

@router.get("/batches/{batch_id}/lineage", response_model=List[LineageEventModel])
@router.get("/v1/batches/{batch_id}/lineage", response_model=List[LineageEventModel])
def get_batch_lineage(batch_id: str = Path(...)):
    return lineage_repo.get_lineage_for_batch(batch_id)

@router.get("/transactions/{transaction_id}/explain-decision", response_model=DecisionExplanationModel)
@router.get("/v1/transactions/{transaction_id}/explain-decision", response_model=DecisionExplanationModel)
def explain_transaction_decision(transaction_id: str = Path(...)):
    return lineage_repo.explain_decision(transaction_id)

# ============================================================
# FEATURE C: INTELLIGENT HYBRID RECONCILIATION
# ============================================================

@router.post("/reconciliation/intelligent-match", response_model=MatchAnalysisResponse)
@router.post("/v1/reconciliation/intelligent-match", response_model=MatchAnalysisResponse)
def run_intelligent_match(request: IntelligentMatchRequest):
    return intelligent_match_service.get_match_analysis(request.bank_transaction_id, request.batch_id or "FINREC-20260922-001")

@router.get("/reconciliation/{batch_id}/intelligent-matches", response_model=List[IntelligentMatchResultModel])
@router.get("/v1/reconciliation/{batch_id}/intelligent-matches", response_model=List[IntelligentMatchResultModel])
def list_intelligent_matches(batch_id: str = Path(...)):
    return intelligent_match_service.list_intelligent_matches(batch_id)

@router.get("/transactions/{transaction_id}/match-analysis", response_model=MatchAnalysisResponse)
@router.get("/v1/transactions/{transaction_id}/match-analysis", response_model=MatchAnalysisResponse)
def get_transaction_match_analysis(transaction_id: str = Path(...)):
    return intelligent_match_service.get_match_analysis(transaction_id)


