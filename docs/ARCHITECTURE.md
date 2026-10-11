# FinRecon — System Architecture Document

## System Objectives
**FinRecon** is designed to provide high-throughput, deterministic transaction processing and automated reconciliation for Mainframe batch environments.

## Component Specifications

### 1. Pre-Processing & Deduplication Layer (Assignment 1)
* **Utility**: IBM DFSORT / ICETOOL
* **Input Dataset**: `FINRECON.INPUT.BANK` (100 records, 80 bytes, RECFM=FB, BLKSIZE=27920)
* **Key Specifications**: Primary Key = `Transaction ID` (Columns 13–20, length 8 bytes, character format)
* **Deduplication Strategy**: `SUM FIELDS=NONE` retains the first record occurrence per primary key.
* **Sorting**: Ascending sort (`CH,A`) on columns 13–20.

### 2. Reconciliation Engine (Assignment 2)
* **Program**: `FINREC01.CBL` (IBM Enterprise COBOL)
* **Input 1**: `FINRECON.WORK.BANK` (50 records subset, 80 bytes, Key: Cols 13–20)
* **Input 2**: `FINRECON.WORK.MERCHANT` (50 records, 80 bytes, Key: Cols 21–28)
* **Algorithm**: Balanced 2-pointer stream merge operating on pre-sorted input streams.
* **Classification Logic**:
  * `MATCHED`: Key Match + Amount Match + Status Match -> `OUTPUT.MATCHED`
  * `AMOUNT-MISMATCH`: Key Match + Amount Difference -> `OUTPUT.EXCEPTION`
  * `STATUS-MISMATCH`: Key Match + Status Difference -> `OUTPUT.EXCEPTION`
  * `MISSING-IN-BANK`: Key present in Merchant feed only -> `OUTPUT.MISSING`
  * `MISSING-IN-MERCHANT`: Key present in Bank feed only -> `OUTPUT.MISSING`

### 3. REXX Audit Layer (Assignment 3)
* **Script**: `FINREXX.REX`
* **Input Dataset**: `FINRECON.INPUT.AUDIT` (120 records, 100 bytes, Key: Cols 25–32)
* **Data Structures**: REXX Stem variables (`INREC.`, `OUTREC.`, `seen.`, `KEYS.`)
* **Processing**: Performs `EXECIO` I/O operations, stem-array hash deduplication, in-memory array sorting, and summary report generation.

### 4. Data Control & Validation Controller (Assignment 4)
* **Jobs**: `VAL01PAS.JCL` and `VAL02FAI.JCL`
* **Utility**: DFSORT + ICETOOL
* **Sorting**: Descending sort (`CH,D`) on Primary Key columns 13–20.
* **Count Validation**: Compares record count of source dataset vs target dataset.
* **Conditional Disposition**:
  * **Equal Count**: `DISP=(NEW,CATLG,DELETE)` catalogs output dataset (`RC=00`).
  * **Unequal Count**: `ICETOOL` / conditional JCL triggers `RC=12` and purges dataset via `IEFBR14`.

### 5. Summary Reporting Layer (Phase 8)
* **Program**: `FINRPT01.CBL`
* **Output Dataset**: `FINRECON.REPORT.SUMMARY` (133 bytes, RECFM=FBA, Carriage Control)
* **Calculations**: Accumulates matched counts/amounts, exception counts/amounts, missing counts/amounts, and total monetary discrepancy.
