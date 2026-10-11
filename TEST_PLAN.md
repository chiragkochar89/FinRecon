# FinRecon — Master System Test Plan & Final Validation Report

## System Test Strategy

The **FinRecon** test plan ensures that all existing faculty assignment test cases (**TC01–TC08**) remain 100% operational, while introducing system-level API and adapter integration test cases (**TC09–TC15**), Phase 3 control-total tests (**TC-P3**), Phase 4 exception triage tests (**TC-P4**), and Phase 5 security, persistence, and reporting tests (**TC-P5**).

---

## Comprehensive Test Case Matrix

### 1. Master Baseline & System Test Cases

| Test ID | Category | Test Objective & Description | Expected Result | Return Code | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC01** | Assignment 2 | Normal Successful Reconciliation | 30 Records matched cleanly. 0 Exceptions. | `RC=00` | PASS |
| **TC02** | Assignment 1 & 3| Duplicate Transaction Detection | 10 Bank dups removed (Assign 1). 15 Audit dups removed (Assign 3). | `RC=00` | PASS |
| **TC03** | Assignment 2 | Amount Mismatch Detection | 5 Amount mismatches detected and routed to `OUTPUT.EXCEPTION`. | `RC=04` | PASS |
| **TC04** | Assignment 2 | Status Mismatch Detection | 5 Status mismatches detected and routed to `OUTPUT.EXCEPTION`. | `RC=04` | PASS |
| **TC05** | Assignment 2 | Transaction Missing from Bank | 10 Missing-in-Bank records detected and written to `OUTPUT.MISSING`. | `RC=04` | PASS |
| **TC06** | Assignment 2 | Transaction Missing from Merchant | 10 Missing-in-Merchant records detected and written to `OUTPUT.MISSING`. | `RC=04` | PASS |
| **TC07** | Assignment 4 | Record Count Equal (JCL Success) | Counts match (90 == 90). File `OUTPUT.VALIDATE` retained. | `RC=00` | PASS |
| **TC08** | Assignment 4 | Record Count Mismatch (JCL Failure) | Mismatch detected (90 != 89). Error logged. File purged. | `RC=12` | PASS |
| **TC09** | System Control | Amount Control Total Success | Input amount == Output amount ($125,450.00). | `RC=00` | PASS |
| **TC10** | System Control | Amount Control Total Failure | Input amount != Output amount ($125,450.00 vs $124,950.00). | `RC=12` | PASS |
| **TC11** | File Validation | Invalid Record Length Detection | Record length != 80 bytes. Flagged during file validation. | `RC=08` | PASS |
| **TC12** | File Validation | Empty Input Dataset Handling | Empty dataset submitted. System flags empty file error. | `RC=08` | PASS |
| **TC13** | Exception Engine| Multiple Exception Classification | Multiple exceptions present. Flagged with proper reason code & severity. | `RC=04` | PASS |
| **TC14** | Pipeline Control| Step Failure Abort | Step failure triggers conditional execution jump, preventing step cascade. | `RC=12` | PASS |
| **TC15** | Adapter Engine | Mode Configuration Verification | Adapter returns correct environment mode badge (`LOCAL_DEMO` / `REAL_MAINFRAME`). | `HTTP 200` | PASS |

---

### 2. Phase 3 — Financial Control Totals Test Matrix

| Test ID | Category | Objective | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-P3-01** | Financial Equation | Accounting Equation Verification | Bank ($62,525.00) = Matched ($37,515) + Amt Mismatch ($6,252.50) + Stat Mismatch ($6,252.50) + Missing Merchant ($12,505.00) | PASS |
| **TC-P3-02** | Reason Codes | Standardized Reason Code `RCN-101` | 5 Amount mismatches flagged with `RCN-101` | PASS |
| **TC-P3-03** | Reason Codes | Standardized Reason Code `RCN-103` | 10 Missing Bank records flagged with `RCN-103` | PASS |
| **TC-P3-04** | Reason Codes | Standardized Reason Code `RCN-104` | 10 Missing Merchant records flagged with `RCN-104` | PASS |
| **TC-P3-05** | Reason Codes | Standardized Reason Code `RCN-102` | 5 Status mismatches flagged with `RCN-102` | PASS |
| **TC-P3-11** | Severity Rules | High Discrepancy Threshold | Discrepancies $\ge \$1,000.00$ classified as `CRITICAL` | PASS |
| **TC-P3-12** | API Summary | Control Total Integrity | API returns accurate totals ($62,525.00 / $37,515.00) | PASS |
| **TC-P3-14** | Mode Check | Local Demo Environment Badge | Correct `LOCAL_DEMO` execution badge rendered | PASS |

---

### 3. Phase 4 — Exception Management & Triage Test Matrix

| Test ID | Category | Objective | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-P4-01** | Exception API | List Exceptions Endpoint | `GET /api/v1/exceptions` returns full 30 exceptions | PASS |
| **TC-P4-02** | Filtering | Filter by Severity | `CRITICAL` filter returns 20 items, `HIGH` returns 10 items | PASS |
| **TC-P4-03** | Filtering | Filter by Reason Code | `RCN-101` filter returns 5 amount mismatches | PASS |
| **TC-P4-04** | Filtering | Filter by Triage Status | `UNASSIGNED` filter returns initial unassigned exceptions | PASS |
| **TC-P4-05** | Search | Search by Transaction ID | Search `TXN10031` returns specific exception item | PASS |
| **TC-P4-06** | Workflow | Assign Exception to Analyst | Assigns `analyst01`, auto-transitions `UNASSIGNED` $\rightarrow$ `IN_REVIEW` | PASS |
| **TC-P4-07** | Validation | Reject Empty Assignee | Assigning whitespace returns `HTTP 400 Bad Request` | PASS |
| **TC-P4-08** | Workflow | Move `UNASSIGNED` $\rightarrow$ `IN_REVIEW` | Status updated to `IN_REVIEW` | PASS |
| **TC-P4-09** | Validation | Reject Invalid Transition | `UNASSIGNED` $\rightarrow$ `RESOLVED` directly returns `HTTP 400 Bad Request` | PASS |
| **TC-P4-10** | Notes | Add Investigation Note | Append-only note created with author & timestamp | PASS |
| **TC-P4-11** | Validation | Reject Empty Note | Empty note text returns `HTTP 400 Bad Request` | PASS |
| **TC-P4-12** | Workflow | Resolve Exception Case | `IN_REVIEW` $\rightarrow$ `RESOLVED` with resolution code & notes | PASS |
| **TC-P4-13** | Validation | Reject Resolution without Notes | Resolving without notes returns `HTTP 400 Bad Request` | PASS |
| **TC-P4-14** | Workflow | Reject Exception Case | `IN_REVIEW` $\rightarrow$ `REJECTED` with rejection code & notes | PASS |
| **TC-P4-15** | Audit Trail | Operational Audit Logging | Audit events created for assignment, notes, and status changes | PASS |
| **TC-P4-16** | Financial Safety | Financial Results Immutability | **Strict Verification**: `bank_amount`, `merchant_amount`, `amount_difference`, `reason_code` remain UNCHANGED | PASS |
| **TC-P4-17** | Summary API | Dashboard Operational Metrics | Summary endpoint returns open exposure and case breakdown | PASS |
| **TC-P4-18** | Local Demo | Demo Triage Workflow | Local demo adapter seamlessly handles operational triage workflow | PASS |
| **TC-P4-19** | Error Handling| Unknown Exception 404 | Requesting non-existent exception returns `HTTP 404 Not Found` | PASS |
| **TC-P4-20** | Frontend Build| TypeScript & Vite Build | `tsc && vite build` succeeds with zero errors | PASS |

---

### 4. Phase 5 — Audit, Security Hardening & Export Reporting Test Matrix

| Test ID | Category | Objective | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-P5-01** | Persistence | SQLite Initialization | Verifies `finrecon_local.db` exists and seeds 30 exceptions | PASS |
| **TC-P5-02** | Persistence | Exception Retrieval | Retrieves single exception (`EXC-10031`) with amounts and status | PASS |
| **TC-P5-03** | Persistence | Investigation Note Persistence | Appends note in SQLite and verifies retrieval across connection pool | PASS |
| **TC-P5-04** | Persistence | Operational Audit Event Persistence | Logs audit event in SQLite and verifies audit timeline history | PASS |
| **TC-P5-05** | Persistence | **Explicit Application Restart Test** | Assigns case, adds note, resets repository connections, re-queries DB $\rightarrow$ all triage state & audit history intact | PASS |
| **TC-P5-06** | RBAC Security | Analyst Role Permissions | `ANALYST` identity can assign exceptions and add notes | PASS |
| **TC-P5-07** | RBAC Security | Supervisor Role Permissions | `SUPERVISOR` identity can resolve exception cases with resolution code | PASS |
| **TC-P5-08** | RBAC Security | **Server-Side 403 Enforcement** | `ANALYST` attempting resolution or report download is rejected with `HTTP 403 Forbidden` and `SECURITY_DENIED` logged | PASS |
| **TC-P5-09** | Security Input| Request Input Validation | Rejects empty assignee strings (`HTTP 400`) and negative pagination skip (`HTTP 422`) | PASS |
| **TC-P5-10** | Hardening | Security Response Headers | Verifies `nosniff`, `DENY`, `Content-Security-Policy`, and `strict-origin-when-cross-origin` | PASS |
| **TC-P5-11** | Hardening | CORS Headers | Verifies preflight CORS responses for authorized frontend origins | PASS |
| **TC-P5-12** | Export Engine| Exceptions CSV Export | Downloads `exceptions.csv` with formatted CSV headers and records | PASS |
| **TC-P5-13** | Export Engine| Audit Trail CSV Export | Downloads `audit.csv` containing full operational audit trail | PASS |
| **TC-P5-14** | Export Engine| Reconciliation Excel Export | Generates multi-tab `reconciliation.xlsx` workbook (`openpyxl`) | PASS |
| **TC-P5-15** | Export Engine| Auditor Summary PDF Export | Generates print-ready `reconciliation.pdf` document (`ReportLab`) | PASS |
| **TC-P5-16** | Audit Trail | Report Export Logging | Generating reports creates `REPORT_EXPORTED` audit log entry | PASS |
| **TC-P5-17** | Filtering | Multi-Parameter Exception Search | Filters exceptions by `severity=CRITICAL&reason_code=RCN-104` | PASS |
| **TC-P5-18** | Filtering | Audit Role Filtering | Filters audit timeline by `role=SUPERVISOR` | PASS |
| **TC-P5-19** | API Engine | Pagination Support | Paginates exception listing with `skip=5&limit=10` | PASS |
| **TC-P5-20** | Immutability| Financial Immutability Protection | **Strict Verification**: Operational triage actions do NOT mutate bank amount, merchant amount, difference, or reason code | PASS |
| **TC-P5-21** | Identity UI | Demo Identity Mode Badge | Displays `LOCAL_DEMO` identity switcher notice on UI | PASS |
| **TC-P5-22** | Mainframe Mode| Real Mainframe Isolation | `RealMainframeAdapter` raises `NotImplementedError` when unconfigured | PASS |

---

### 5. Phase 6 — Advanced Research & Innovation Test Matrix

| Test ID | Category | Objective | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-P6-01** | Self-Healing | Control Failure Simulation | `POST /api/v1/recovery/simulate-failure` sets stage `FAILED_CONTROL` (`RC=12`) | PASS |
| **TC-P6-02** | Self-Healing | Stage Checkpoint Replay & Recovery | `POST /api/v1/batches/{id}/recover` replays stage, restores totals & sets `RECOVERED` (`RC=00`) | PASS |
| **TC-P6-03** | Lineage Graph| Transaction Lineage Provenance | `GET /api/v1/transactions/{id}/lineage` returns 10-step lifecycle provenance | PASS |
| **TC-P6-04** | Lineage Graph| Deterministic Decision Explanation | `GET /api/v1/transactions/{id}/explain-decision` returns rule decision rationale | PASS |
| **TC-P6-05** | Intelligent AI| Secondary Similarity Scoring | `POST /api/v1/reconciliation/intelligent-match` returns candidate match scores | PASS |
| **TC-P6-06** | Intelligent AI| 6-Element Feature Vector Scoring | Computes amount, date, merchant, reference, account, and status similarity vectors | PASS |
| **TC-P6-07** | Intelligent AI| Candidate High-Confidence Routing | Candidate match `M-89321` scored 0.96 (`HIGH` confidence, `AUTO_MATCH` recommendation) | PASS |
| **TC-P6-08** | API Engine | Phase 6 Endpoint Integration | API suite handles control recovery, lineage tree, and AI match endpoints | PASS |
| **TC-P6-09** | Regression | Full System Regression Protection | Phase 3/4/5 functionality intact across test execution | PASS |

---

### 6. Phase 7 — Dynamic Reconciliation, Sync & Pipeline Execution Test Matrix

| Test ID | Module | Objective | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-P7B-01** | `test_phase7b` | Valid Record Parsing | Parses 100 bank records and 50 merchant records without format errors | PASS |
| **TC-P7B-02** | `test_phase7b` | Malformed & Missing Record Handling | Catches invalid record length (<80 bytes) and raises FileNotFoundError on missing feeds | PASS |
| **TC-P7B-03** | `test_phase7b` | Bank Feed DFSORT Deduplication | 100 raw records $\rightarrow$ 90 unique records, 10 duplicate records accurately identified | PASS |
| **TC-P7B-04** | `test_phase7b` | Dynamic Reconciliation & Accounting Equations | Verifies 30 matched ($37,515.00), 5 amt mismatch, 5 stat mismatch, 10 missing bank, 10 missing merch; equation balanced | PASS |
| **TC-P7B-05** | `test_phase7b` | Amount vs. Status Mismatch Precedence | Amount Mismatch (`RCN-101`) takes precedence over Status Mismatch (`RCN-102`) | PASS |
| **TC-P7B-06** | `test_phase7b` | End-to-End API & Export Integrity | Batch API, checkpoint telemetry, CSV, XLSX, and PDF exports all align with dynamic totals | PASS |
| **TC-P7D-01** | `test_phase7d` | Source Amounts End-to-End Pipeline Survival | Actual source amounts survive parsing, classification, SQLite persistence, and exports | PASS |
| **TC-P7D-02** | `test_phase7d` | Bank Feed Deduplication Policy | DFSORT deduplication logic strictly mirrors mainframe behavior | PASS |
| **TC-P7D-03** | `test_phase7d` | Batch Re-run Idempotency | Re-executing batch produces identical records, control totals, and audit counts without orphan records | PASS |
| **TC-P7D-04** | `test_phase7d` | Multi-Batch Isolation | Separate batches do not collide or overwrite other batch exceptions | PASS |
| **TC-P7D-05** | `test_phase7d` | Missing Records Source Preservation | Missing bank records retain merchant details; missing merchant records retain bank details | PASS |
| **TC-P7D-06** | `test_phase7d` | API Summary & SQLite Consistency | Dashboard summary figures match persisted exception records in SQLite | PASS |
| **TC-P7D-07** | `test_phase7d` | Export Outputs Reconciliation Consistency | CSV, XLSX, and PDF export outputs contain verified transaction amounts and statuses | PASS |
| **TC-P7D-08** | `test_phase7d` | Gross vs Net Financial Exposure | Correctly distinguishes gross exposure sum ($54,913.50) from net source variance ($33,318.50) | PASS |
| **TC-P7D-09** | `test_phase7d` | Accounting Control Metrics Definitions | Validates precision and decimal accuracy across accounting equations | PASS |
| **TC-P7D-10** | `test_phase7d` | RBAC Security & Audit Event Logging | Ensures role violations log `SECURITY_DENIED` and valid actions log audit records | PASS |
| **TC-P7D-11** | `test_phase7d` | Known Batch Query Filtering | API correctly filters exceptions and controls by specified batch ID | PASS |
| **TC-P7D-12** | `test_phase7d` | Unknown Batch Query Handling | Querying non-existent batch returns empty dataset gracefully | PASS |
| **TC-P7D-13** | `test_phase7d` | Omitted Batch Fallback Query | Querying without batch parameter returns global operational items | PASS |
| **TC-P7D-14** | `test_phase7d` | Transaction Rollback on Database Error | Atomic SQLite transaction rolls back if exception insertion fails | PASS |
| **TC-P7D-15** | `test_phase7d` | Batch Read & Explicit Submission | Verifies batch execution workflow via explicit submission API | PASS |
| **TC-PIPE-01** | `test_pipeline` | Initial PENDING Pipeline State | All 8 stages initialize in `PENDING` before batch execution | PASS |
| **TC-PIPE-02** | `test_pipeline` | Step-by-Step Batch Execution Stream | 8 stages transition sequentially (`PENDING` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED`) with telemetry | PASS |
| **TC-PIPE-03** | `test_pipeline` | Repeated Execution Consistency | Re-running pipeline cleanly resets and executes without residual corruption | PASS |
| **TC-PIPE-04** | `test_pipeline` | Control Failure Halts Downstream | Control failure simulation sets stage to `FAILED_CONTROL` and blocks downstream execution | PASS |
| **TC-PIPE-05** | `test_pipeline` | Pipeline Role-Based Access Control | Both user and supervisor roles can execute batches; supervisor retains report privileges | PASS |
| **TC-PIPE-06** | `test_pipeline` | Self-Healing Recovery & Verification | Stage replay heals `FAILED_CONTROL` stage to `RECOVERED` with telemetry updated | PASS |
| **TC-PIPE-07** | `test_pipeline` | State Persistence on Page Refresh | Pipeline stage state and execution results persist across browser reloads | PASS |
| **TC-PIPE-08** | `test_pipeline` | Pipeline Reset to Initial State | Reset action restores all 8 pipeline stages to `PENDING` | PASS |
| **TC-TXN-01** | `test_txn_detail` | Matched Transaction Lineage Consistency | `TXN10001` consistently renders MATCHED header, RCN-000, $0.00 variance, and provenance | PASS |
| **TC-TXN-02** | `test_txn_detail` | Status Mismatch Consistency | `TXN10036` consistently renders STATUS MISMATCH, RCN-102, AP vs RJ across tabs | PASS |
| **TC-TXN-03** | `test_txn_detail` | Transaction Search by Account & ID | Search indexing accurately resolves transactions by account number (`ACC100000001`) and ID | PASS |
| **TC-FIN-01** | `test_financial` | Financial Control Totals Equation Conservation | Verifies Bank ($94,136.00) and Merchant ($60,817.50) conservation equations | PASS |
| **TC-FIN-02** | `test_financial` | Dynamic Batch Report Content | Formatted text report displays exact calculated figures rather than static mock values | PASS |
| **TC-FIN-03** | `test_financial` | HTTP 403 Forbidden Response Detail | Standardized error response detail when unauthorized action attempted | PASS |
| **TC-FIN-04** | `test_financial` | Assignee Lifecycle Preservation | Assignee remains attached across subsequent exception state transitions | PASS |
| **TC-FIN-05** | `test_financial` | Report Formatting with Arbitrary Totals | Report formatter correctly balances arbitrary financial control structures | PASS |
| **TC-FIN-06** | `test_financial` | Missing Input Feeds Actionable Error | Explicit, actionable error returned if input feeds are missing (no fabricated totals) | PASS |
| **TC-FIN-07** | `test_financial` | Strict Reconciliation Engine Alignment | Local demo adapter directly delegates calculations to `ReconciliationEngine` | PASS |

---

### 7. Phase 8 — Authentication & Role-Based Access Control (RBAC) Test Matrix

| Test ID | Module | Objective | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-AUTH-01** | `test_auth` | Argon2id Password Hashing | Verifies Argon2id hash generation and verification (`argon2-cffi`) | PASS |
| **TC-AUTH-02** | `test_auth` | User Login Success | `finrecon_user` logs in successfully, receives session token and `USER` role | PASS |
| **TC-AUTH-03** | `test_auth` | Supervisor Login Success | `finrecon_supervisor` logs in successfully, receives session token and `SUPERVISOR` role | PASS |
| **TC-AUTH-04** | `test_auth` | Login Failure — Invalid Password | Rejects incorrect password with `HTTP 401 Unauthorized` and increments failed count | PASS |
| **TC-AUTH-05** | `test_auth` | Login Failure — Unknown User | Rejects non-existent username with `HTTP 401 Unauthorized` | PASS |
| **TC-AUTH-06** | `test_auth` | Account Lockout Protection | Locks account after 5 consecutive failed attempts; rejects subsequent attempts with `HTTP 423` | PASS |
| **TC-AUTH-07** | `test_auth` | Authenticated `/auth/me` Endpoint | Returns user details, role, and permissions for active session token | PASS |
| **TC-AUTH-08** | `test_auth` | Unauthenticated `/auth/me` Endpoint | Rejects missing session token with `HTTP 401 Unauthorized` | PASS |
| **TC-AUTH-09** | `test_auth` | Invalid Token `/auth/me` Endpoint | Rejects forged/expired token with `HTTP 401 Unauthorized` | PASS |
| **TC-AUTH-10** | `test_auth` | Session Logout Revocation | `POST /auth/logout` invalidates session token; subsequent requests receive `HTTP 401` | PASS |
| **TC-AUTH-11** | `test_auth` | RBAC: User Forbidden from Reports | User session attempting report export is rejected with `HTTP 403 Forbidden` | PASS |
| **TC-AUTH-12** | `test_auth` | RBAC: Supervisor Permitted Reports | Supervisor session successfully downloads CSV, XLSX, and PDF reports | PASS |
| **TC-AUTH-13** | `test_auth` | RBAC: User Forbidden from Case Resolution | User session attempting exception resolution is rejected with `HTTP 403 Forbidden` | PASS |
| **TC-AUTH-14** | `test_auth` | RBAC: Supervisor Permitted Case Resolution | Supervisor session successfully resolves exception cases with resolution code | PASS |

---

## Final Validation Summary

The FinRecon platform has undergone comprehensive validation across automated testing, standalone test harnesses, frontend production builds, manual end-to-end testing workflows, and export report verification.

### 1. Automated Testing Execution Summary

| Validation Suite | Target Component | Test Count | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Pytest Backend & Integration Suite** | All 11 test modules (APIs, DB, Auth, RBAC, Recon, Reports, Pipeline) | 114 / 114 | **114 PASSED** | **PASS** |
| **Faculty Assignment 1 Harness** | `DFSORT` Deduplication & Ascending Sort | 1 / 1 | **`RC=00`** | **PASS** |
| **Faculty Assignment 2 Harness** | `COBOL` 5-Way Reconciliation Engine | 1 / 1 | **`RC=04`** | **PASS** |
| **Faculty Assignment 3 Harness** | `TSO REXX` Audit Stem Deduplication | 1 / 1 | **`RC=00`** | **PASS** |
| **Faculty Assignment 4 Success Harness**| `JCL` Record Count Equal Validation | 1 / 1 | **`RC=00`** | **PASS** |
| **Faculty Assignment 4 Fail Harness** | `JCL` Count Mismatch Purge Execution | 1 / 1 | **`RC=12`** | **PASS** |
| **Project Report Generator Harness** | `COBOL` Management Summary Report | 1 / 1 | **`RC=04`** | **PASS** |
| **Frontend Production Build** | TypeScript Compiler & Vite Bundler | 1 / 1 | **`0 Errors`** | **PASS** |

---

### 2. Validation Categorization

- **Automated Unit & Integration Testing**: Executed via Pytest (`python -m pytest tests/ backend/tests/ -v`). Verifies 114 test cases spanning API routes, SQLite persistence, Argon2id authentication, session management, RBAC enforcement, dynamic reconciliation equations, pipeline execution telemetry, self-healing recovery, transaction lineage, and intelligent similarity scoring.
- **Manual End-to-End Validation**: Executed interactively via web dashboard (`http://localhost:5173`). Verifies login authentication, file upload validation, live batch pipeline execution stream, exception triage workflow, transaction lineage drawer, and report downloads.
- **Auditor Report Export Verification**: Verified downloading CSV, multi-tab Excel (`.xlsx`), and PDF (`.pdf`) packages. Inspected for formatting accuracy, data completeness, dynamic control total alignment, and inclusion of execution mode disclosures.

---

### 3. Final Overall Status

$$\mathbf{\text{FINAL SYSTEM VALIDATION: PASS (114/114 PASSED - 100\% VERIFIED)}}$$

---

## Team & Contributors

- **Chirag Kochar**
- **Prem Palhade**
- **Zainab Pirjade**
