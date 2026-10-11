# FinRecon — Advanced Architecture Extensions (Phase 10)
## Optional VSAM KSDS & DB2 Integration Layer

While the core **FinRecon** batch engine operates on high-performance z/OS Physical Sequential (PS) datasets, the system architecture is designed to seamlessly scale into enterprise VSAM and DB2 relational storage.

---

## 1. VSAM KSDS Master Transaction Repository

### IDCAMS Allocation Parameters
To support fast random access and keyed lookup by `Transaction ID`, the clean Bank transaction file can be loaded into a VSAM Key-Sequenced Dataset (KSDS).

```jcl
//DEFVSAM  EXEC PGM=IDCAMS
//SYSPRINT DD SYSOUT=*
//SYSIN    DD *
  DELETE &HLQ..FINRECON.VSAM.BANK.KSDS CLUSTER PURGE
  
  DEFINE CLUSTER ( -
    NAME(&HLQ..FINRECON.VSAM.BANK.KSDS) -
    INDEXED -
    KEYS(8 12) -
    RECORDSIZE(80 80) -
    FREESPACE(10 10) -
    SHAREOPTIONS(2 3) -
    VOLUMES(SYSDA) -
    CYLINDERS(2 1) -
  ) -
  DATA (NAME(&HLQ..FINRECON.VSAM.BANK.KSDS.DATA)) -
  INDEX (NAME(&HLQ..FINRECON.VSAM.BANK.KSDS.INDEX))
/*
```
* **Key Definition**: `KEYS(8 12)` defines an 8-byte primary key starting at offset 12 (columns 13–20).
* **COBOL VSAM Access**:
```cobol
       FILE-CONTROL.
           SELECT BANK-VSAM-FILE ASSIGN TO BNKVSAM
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS BNK-VSAM-TRXN-ID
               FILE STATUS IS WS-VSAM-STATUS.
```

---

## 2. DB2 Audit & Discrepancy Reporting Layer

### DB2 Table DDL (`FINRECON_AUDIT_TBL`)
For enterprise compliance, reporting, and SQL analytics, exception records are staged into DB2 for z/OS.

```sql
CREATE TABLE FINRECON_AUDIT_TBL (
    TRXN_ID         CHAR(8)       NOT NULL,
    ACCT_NO         CHAR(12)      NOT NULL,
    TRXN_DATE       DATE          NOT NULL,
    BANK_AMT        DECIMAL(12,2) NOT NULL,
    MERCH_AMT       DECIMAL(12,2) NOT NULL,
    DISCREP_AMT     DECIMAL(12,2) NOT NULL,
    BANK_STATUS     CHAR(2)       NOT NULL,
    MERCH_STATUS    CHAR(2)       NOT NULL,
    RECON_CATEGORY  VARCHAR(20)   NOT NULL,
    AUDIT_TIMESTAMP TIMESTAMP     NOT NULL DEFAULT CURRENT TIMESTAMP,
    PRIMARY KEY (TRXN_ID)
) IN FINDB.FINTS;

CREATE UNIQUE INDEX FINRECON_IX1 
    ON FINRECON_AUDIT_TBL (TRXN_ID);
```

### Embedded SQL COBOL Fragment
```cobol
       EXEC SQL
           INSERT INTO FINRECON_AUDIT_TBL
           ( TRXN_ID, ACCT_NO, TRXN_DATE, BANK_AMT, MERCH_AMT,
             DISCREP_AMT, BANK_STATUS, MERCH_STATUS, RECON_CATEGORY )
           VALUES
           ( :WS-TRXN-ID, :WS-ACCT-NO, :WS-TRXN-DATE, :WS-BANK-AMT,
             :WS-MERCH-AMT, :WS-DISCREP-AMT, :WS-BANK-STAT,
             :WS-MERCH-STAT, :WS-RECON-CAT )
       END-EXEC.
```
