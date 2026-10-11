       IDENTIFICATION DIVISION.
       PROGRAM-ID. FINRPT01.
      *----------------------------------------------------------------*
      * FINRECON - PHASE 8: SUMMARY & AUDIT REPORT GENERATOR           *
      * OBJECTIVE: READ RECONCILIATION OUTPUT FILES (MATCHED,          *
      *            EXCEPTION, MISSING) AND GENERATE AN AUDIT-READY     *
      *            MANAGEMENT REPORT WITH CARRIAGE CONTROL (RECFM=FBA).*
      *----------------------------------------------------------------*
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT MATCH-FILE ASSIGN TO MATCHIN
               ORGANIZATION IS SEQUENTIAL.
           SELECT EXCP-FILE  ASSIGN TO EXCPIN
               ORGANIZATION IS SEQUENTIAL.
           SELECT MISS-FILE  ASSIGN TO MISSIN
               ORGANIZATION IS SEQUENTIAL.
           SELECT RPT-FILE   ASSIGN TO RPTFILE
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  MATCH-FILE.
       01  MATCH-REC.
           05  FILLER               PIC X(34).
           05  M-AMT                PIC 9(10)V99.
           05  FILLER               PIC X(34).

       FD  EXCP-FILE.
       01  EXCP-REC.
           05  FILLER               PIC X(34).
           05  E-AMT                PIC 9(10)V99.
           05  FILLER               PIC X(34).

       FD  MISS-FILE.
       01  MISS-REC.
           05  FILLER               PIC X(34).
           05  S-AMT                PIC 9(10)V99.
           05  FILLER               PIC X(34).

       FD  RPT-FILE.
       01  RPT-REC                  PIC X(133).

       WORKING-STORAGE SECTION.
       01  WS-EOF-FLAGS.
           05  WS-MATCH-EOF         PIC X(01) VALUE 'N'.
           05  WS-EXCP-EOF          PIC X(01) VALUE 'N'.
           05  WS-MISS-EOF          PIC X(01) VALUE 'N'.

       01  WS-COUNTERS.
           05  WS-MATCH-CNT         PIC 9(05) VALUE ZERO.
           05  WS-EXCP-CNT          PIC 9(05) VALUE ZERO.
           05  WS-MISS-CNT          PIC 9(05) VALUE ZERO.
           05  WS-TOTAL-PROCESSED   PIC 9(05) VALUE ZERO.

       01  WS-TOTALS.
           05  WS-MATCH-AMT-TOT     PIC 9(12)V99 VALUE ZERO.
           05  WS-EXCP-AMT-TOT      PIC 9(12)V99 VALUE ZERO.
           05  WS-MISS-AMT-TOT      PIC 9(12)V99 VALUE ZERO.
           05  WS-TOTAL-DISCREPANCY PIC 9(12)V99 VALUE ZERO.

       01  WS-FORMATTED-NUMS.
           05  WS-FMT-MATCH-AMT     PIC $$$,$$$,$$9.99.
           05  WS-FMT-EXCP-AMT      PIC $$$,$$$,$$9.99.
           05  WS-FMT-MISS-AMT      PIC $$$,$$$,$$9.99.
           05  WS-FMT-DISCREP-AMT   PIC $$$,$$$,$$9.99.

       01  RPT-HEADER-1.
           05  FILLER               PIC X(01) VALUE '1'.
           05  FILLER               PIC X(132) VALUE
           '==========================================================='
           & '========================================'.

       01  RPT-HEADER-2.
           05  FILLER               PIC X(01) VALUE ' '.
           05  FILLER               PIC X(50) VALUE
           'FINRECON — FINANCIAL TRANSACTION RECONCILIATION '.
           05  FILLER               PIC X(20) VALUE 'AUDIT REPORT'.
           05  FILLER               PIC X(62) VALUE SPACES.

       01  RPT-HEADER-3.
           05  FILLER               PIC X(01) VALUE ' '.
           05  FILLER               PIC X(30) VALUE
           'BATCH ID    : FINREC-BATCH-001'.
           05  FILLER               PIC X(30) VALUE
           'PROCESS DATE: 2026-09-22'.
           05  FILLER               PIC X(72) VALUE SPACES.

       01  RPT-LINE-STARS.
           05  FILLER               PIC X(01) VALUE ' '.
           05  FILLER               PIC X(132) VALUE ALL '-'.

       01  RPT-DETAIL-LINE.
           05  FILLER               PIC X(01) VALUE ' '.
           05  RPT-LABEL            PIC X(35).
           05  RPT-VALUE-CNT        PIC ZZZ,ZZ9.
           05  FILLER               PIC X(10) VALUE SPACES.
           05  RPT-VALUE-AMT        PIC X(20).
           05  FILLER               PIC X(61) VALUE SPACES.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-INITIALIZATION
           PERFORM 2000-PROCESS-MATCHED
           PERFORM 3000-PROCESS-EXCEPTIONS
           PERFORM 4000-PROCESS-MISSING
           PERFORM 5000-GENERATE-REPORT
           PERFORM 6000-CLOSE-FILES
           GOBACK.

       1000-INITIALIZATION.
           OPEN INPUT  MATCH-FILE EXCP-FILE MISS-FILE
                OUTPUT RPT-FILE.

       2000-PROCESS-MATCHED.
           READ MATCH-FILE AT END MOVE 'Y' TO WS-MATCH-EOF END-READ
           PERFORM UNTIL WS-MATCH-EOF = 'Y'
               ADD 1 TO WS-MATCH-CNT
               ADD M-AMT TO WS-MATCH-AMT-TOT
               READ MATCH-FILE AT END MOVE 'Y' TO WS-MATCH-EOF END-READ
           END-PERFORM.

       3000-PROCESS-EXCEPTIONS.
           READ EXCP-FILE AT END MOVE 'Y' TO WS-EXCP-EOF END-READ
           PERFORM UNTIL WS-EXCP-EOF = 'Y'
               ADD 1 TO WS-EXCP-CNT
               ADD E-AMT TO WS-EXCP-AMT-TOT
               READ EXCP-FILE AT END MOVE 'Y' TO WS-EXCP-EOF END-READ
           END-PERFORM.

       4000-PROCESS-MISSING.
           READ MISS-FILE AT END MOVE 'Y' TO WS-MISS-EOF END-READ
           PERFORM UNTIL WS-MISS-EOF = 'Y'
               ADD 1 TO WS-MISS-CNT
               ADD S-AMT TO WS-MISS-AMT-TOT
               READ MISS-FILE AT END MOVE 'Y' TO WS-MISS-EOF END-READ
           END-PERFORM.

       5000-GENERATE-REPORT.
           COMPUTE WS-TOTAL-PROCESSED = WS-MATCH-CNT + WS-EXCP-CNT
                                        + WS-MISS-CNT
           COMPUTE WS-TOTAL-DISCREPANCY = WS-EXCP-AMT-TOT 
                                        + WS-MISS-AMT-TOT

           MOVE WS-MATCH-AMT-TOT     TO WS-FMT-MATCH-AMT
           MOVE WS-EXCP-AMT-TOT      TO WS-FMT-EXCP-AMT
           MOVE WS-MISS-AMT-TOT      TO WS-FMT-MISS-AMT
           MOVE WS-TOTAL-DISCREPANCY TO WS-FMT-DISCREP-AMT

           WRITE RPT-REC FROM RPT-HEADER-1
           WRITE RPT-REC FROM RPT-HEADER-2
           WRITE RPT-REC FROM RPT-HEADER-3
           WRITE RPT-REC FROM RPT-LINE-STARS

           MOVE 'MATCHED TRANSACTIONS' TO RPT-LABEL
           MOVE WS-MATCH-CNT TO RPT-VALUE-CNT
           MOVE WS-FMT-MATCH-AMT TO RPT-VALUE-AMT
           WRITE RPT-REC FROM RPT-DETAIL-LINE

           MOVE 'AMOUNT / STATUS MISMATCHES' TO RPT-LABEL
           MOVE WS-EXCP-CNT TO RPT-VALUE-CNT
           MOVE WS-FMT-EXCP-AMT TO RPT-VALUE-AMT
           WRITE RPT-REC FROM RPT-DETAIL-LINE

           MOVE 'MISSING IN BANK / MERCHANT' TO RPT-LABEL
           MOVE WS-MISS-CNT TO RPT-VALUE-CNT
           MOVE WS-FMT-MISS-AMT TO RPT-VALUE-AMT
           WRITE RPT-REC FROM RPT-DETAIL-LINE

           WRITE RPT-REC FROM RPT-LINE-STARS

           MOVE 'TOTAL TRANSACTION DISCREPANCY' TO RPT-LABEL
           MOVE WS-EXCP-CNT TO RPT-VALUE-CNT
           MOVE WS-FMT-DISCREP-AMT TO RPT-VALUE-AMT
           WRITE RPT-REC FROM RPT-DETAIL-LINE

           WRITE RPT-REC FROM RPT-LINE-STARS.

       6000-CLOSE-FILES.
           CLOSE MATCH-FILE EXCP-FILE MISS-FILE RPT-FILE.
