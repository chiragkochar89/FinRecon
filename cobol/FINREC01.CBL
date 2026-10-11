       IDENTIFICATION DIVISION.
       PROGRAM-ID. FINREC01.
      *----------------------------------------------------------------*
      * FINRECON - PHASE 3: ENHANCED COBOL RECONCILIATION ENGINE       *
      * OBJECTIVE: READ TWO 80-BYTE PS FILES (BANK & MERCHANT), MERGE   *
      *            MATCH BY PRIMARY KEY, CLASSIFY INTO 5 CATEGORIES,   *
      *            AND COMPUTE FINANCIAL CONTROL MONETARY ACCUMULATORS.*
      *----------------------------------------------------------------*
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT BANK-FILE    ASSIGN TO BANKIN
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-BANK-STATUS.
               
           SELECT MERCH-FILE   ASSIGN TO MERCHIN
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-MERCH-STATUS.
               
           SELECT MATCH-FILE   ASSIGN TO MATCHOUT
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-MATCH-STATUS.
               
           SELECT EXCP-FILE    ASSIGN TO EXCPOUT
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-EXCP-STATUS.
               
           SELECT MISS-FILE    ASSIGN TO MISSOUT
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-MISS-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  BANK-FILE.
       01  BANK-REC.
           05  BNK-ACCT-NO          PIC X(12).
           05  BNK-TRXN-ID          PIC X(08).  *> KEY: COLS 13-20
           05  BNK-TRXN-DATE        PIC X(08).
           05  BNK-TRXN-TIME        PIC X(06).
           05  BNK-TRXN-AMT         PIC 9(10)V99.
           05  BNK-CURR-CODE        PIC X(03).
           05  BNK-TRXN-TYPE        PIC X(02).
           05  BNK-TRXN-STAT        PIC X(02).
           05  BNK-MERCH-ID         PIC X(08).
           05  BNK-REF-NO           PIC X(15).
           05  FILLER               PIC X(04).

       FD  MERCH-FILE.
       01  MERCH-REC.
           05  MCH-MERCH-ID         PIC X(08).
           05  MCH-ACCT-NO          PIC X(12).
           05  MCH-TRXN-ID          PIC X(08).  *> KEY: COLS 21-28
           05  MCH-TRXN-DATE        PIC X(08).
           05  MCH-TRXN-TIME        PIC X(06).
           05  MCH-TRXN-AMT         PIC 9(10)V99.
           05  MCH-CURR-CODE        PIC X(03).
           05  MCH-TRXN-TYPE        PIC X(02).
           05  MCH-TRXN-STAT        PIC X(02).
           05  MCH-TERM-REF         PIC X(15).
           05  FILLER               PIC X(04).

       FD  MATCH-FILE.
       01  MATCH-REC                PIC X(80).

       FD  EXCP-FILE.
       01  EXCP-REC                 PIC X(80).

       FD  MISS-FILE.
       01  MISS-REC                 PIC X(80).

       WORKING-STORAGE SECTION.
       01  WS-FILE-STATUSES.
           05  WS-BANK-STATUS       PIC X(02) VALUE "00".
           05  WS-MERCH-STATUS      PIC X(02) VALUE "00".
           05  WS-MATCH-STATUS      PIC X(02) VALUE "00".
           05  WS-EXCP-STATUS       PIC X(02) VALUE "00".
           05  WS-MISS-STATUS       PIC X(02) VALUE "00".

       01  WS-FLAGS.
           05  WS-BANK-EOF          PIC X(01) VALUE "N".
               88 BANK-END-OF-FILE            VALUE "Y".
           05  WS-MERCH-EOF         PIC X(01) VALUE "N".
               88 MERCH-END-OF-FILE           VALUE "Y".

       01  WS-HIGH-KEY              PIC X(08) VALUE HIGH-VALUES.

       01  WS-CURR-BANK-KEY         PIC X(08).
       01  WS-CURR-MERCH-KEY        PIC X(08).

       01  WS-COUNTERS.
           05  WS-BANK-READ-CNT     PIC 9(05) VALUE ZERO.
           05  WS-MERCH-READ-CNT    PIC 9(05) VALUE ZERO.
           05  WS-MATCHED-CNT       PIC 9(05) VALUE ZERO.
           05  WS-AMT-MISMATCH-CNT  PIC 9(05) VALUE ZERO.
           05  WS-STAT-MISMATCH-CNT PIC 9(05) VALUE ZERO.
           05  WS-MISS-BANK-CNT     PIC 9(05) VALUE ZERO.
           05  WS-MISS-MERCH-CNT    PIC 9(05) VALUE ZERO.
           05  WS-TOTAL-EXCP-CNT    PIC 9(05) VALUE ZERO.

       01  WS-FINANCIAL-TOTALS.
           05  WS-BANK-AMT-TOT      PIC 9(12)V99 VALUE ZERO.
           05  WS-MERCH-AMT-TOT     PIC 9(12)V99 VALUE ZERO.
           05  WS-MATCHED-AMT-TOT   PIC 9(12)V99 VALUE ZERO.
           05  WS-DISCREPANCY-TOTAL PIC 9(12)V99 VALUE ZERO.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-INITIALIZATION
           PERFORM 2000-RECONCILE-LOOP 
             UNTIL BANK-END-OF-FILE AND MERCH-END-OF-FILE
           PERFORM 3000-GENERATE-SUMMARY
           PERFORM 4000-CLOSE-FILES
           GOBACK.

       1000-INITIALIZATION.
           DISPLAY "FINREC01: STARTING FINANCIAL RECONCILIATION ENGINE".
           OPEN INPUT  BANK-FILE
                       MERCH-FILE
                OUTPUT MATCH-FILE
                       EXCP-FILE
                       MISS-FILE.
           
           IF WS-BANK-STATUS NOT = "00" OR WS-MERCH-STATUS NOT = "00"
               DISPLAY "ERROR OPENING INPUT FILES. BANK=" WS-BANK-STATUS
                       " MERCH=" WS-MERCH-STATUS
               MOVE 12 TO RETURN-CODE
               GOBACK
           END-IF.

           PERFORM 1100-READ-BANK
           PERFORM 1200-READ-MERCHANT.

       1100-READ-BANK.
           READ BANK-FILE
             AT END
               MOVE "Y" TO WS-BANK-EOF
               MOVE WS-HIGH-KEY TO WS-CURR-BANK-KEY
             NOT AT END
               ADD 1 TO WS-BANK-READ-CNT
               ADD BNK-TRXN-AMT TO WS-BANK-AMT-TOT
               MOVE BNK-TRXN-ID TO WS-CURR-BANK-KEY
           END-READ.

       1200-READ-MERCHANT.
           READ MERCH-FILE
             AT END
               MOVE "Y" TO WS-MERCH-EOF
               MOVE WS-HIGH-KEY TO WS-CURR-MERCH-KEY
             NOT AT END
               ADD 1 TO WS-MERCH-READ-CNT
               ADD MCH-TRXN-AMT TO WS-MERCH-AMT-TOT
               MOVE MCH-TRXN-ID TO WS-CURR-MERCH-KEY
           END-READ.

       2000-RECONCILE-LOOP.
           EVALUATE TRUE
             WHEN WS-CURR-BANK-KEY = WS-CURR-MERCH-KEY
               PERFORM 2100-COMPARE-TRANSACTIONS
               PERFORM 1100-READ-BANK
               PERFORM 1200-READ-MERCHANT
             WHEN WS-CURR-BANK-KEY < WS-CURR-MERCH-KEY
               PERFORM 2200-HANDLE-MISSING-MERCHANT
               PERFORM 1100-READ-BANK
             WHEN WS-CURR-BANK-KEY > WS-CURR-MERCH-KEY
               PERFORM 2300-HANDLE-MISSING-BANK
               PERFORM 1200-READ-MERCHANT
           END-EVALUATE.

       2100-COMPARE-TRANSACTIONS.
           IF BNK-TRXN-AMT = MCH-TRXN-AMT AND
              BNK-TRXN-STAT = MCH-TRXN-STAT
               ADD 1 TO WS-MATCHED-CNT
               ADD BNK-TRXN-AMT TO WS-MATCHED-AMT-TOT
               WRITE MATCH-REC FROM BANK-REC
           ELSE
               IF BNK-TRXN-AMT NOT = MCH-TRXN-AMT
                   ADD 1 TO WS-AMT-MISMATCH-CNT
                   ADD 1 TO WS-TOTAL-EXCP-CNT
                   IF BNK-TRXN-AMT > MCH-TRXN-AMT
                       ADD (BNK-TRXN-AMT - MCH-TRXN-AMT) TO WS-DISCREPANCY-TOTAL
                   ELSE
                       ADD (MCH-TRXN-AMT - BNK-TRXN-AMT) TO WS-DISCREPANCY-TOTAL
                   END-IF
                   WRITE EXCP-REC FROM BANK-REC
                   DISPLAY "EXCP: AMOUNT MISMATCH [RCN-101] KEY: " BNK-TRXN-ID
               END-IF
               IF BNK-TRXN-STAT NOT = MCH-TRXN-STAT
                   ADD 1 TO WS-STAT-MISMATCH-CNT
                   ADD 1 TO WS-TOTAL-EXCP-CNT
                   WRITE EXCP-REC FROM BANK-REC
                   DISPLAY "EXCP: STATUS MISMATCH [RCN-102] KEY: " BNK-TRXN-ID
               END-IF
           END-IF.

       2200-HANDLE-MISSING-MERCHANT.
           ADD 1 TO WS-MISS-MERCH-CNT
           ADD 1 TO WS-TOTAL-EXCP-CNT
           ADD BNK-TRXN-AMT TO WS-DISCREPANCY-TOTAL
           WRITE MISS-REC FROM BANK-REC
           DISPLAY "EXCP: MISSING IN MERCHANT [RCN-104] KEY: " BNK-TRXN-ID.

       2300-HANDLE-MISSING-BANK.
           ADD 1 TO WS-MISS-BANK-CNT
           ADD 1 TO WS-TOTAL-EXCP-CNT
           ADD MCH-TRXN-AMT TO WS-DISCREPANCY-TOTAL
           WRITE MISS-REC FROM MERCH-REC
           DISPLAY "EXCP: MISSING IN BANK [RCN-103] KEY: " MCH-TRXN-ID.

       3000-GENERATE-SUMMARY.
           DISPLAY "==================================================".
           DISPLAY "FINRECON — RECONCILIATION & CONTROL TOTAL REPORT  ".
           DISPLAY "==================================================".
           DISPLAY "TOTAL BANK RECORDS READ     : " WS-BANK-READ-CNT.
           DISPLAY "TOTAL BANK MONETARY AMOUNT  : $" WS-BANK-AMT-TOT.
           DISPLAY "TOTAL MERCHANT RECORDS READ : " WS-MERCH-READ-CNT.
           DISPLAY "TOTAL MERCHANT AMOUNT       : $" WS-MERCH-AMT-TOT.
           DISPLAY "--------------------------------------------------".
           DISPLAY "MATCHED TRANSACTIONS        : " WS-MATCHED-CNT.
           DISPLAY "MATCHED MONETARY AMOUNT     : $" WS-MATCHED-AMT-TOT.
           DISPLAY "AMOUNT MISMATCHES [RCN-101] : " WS-AMT-MISMATCH-CNT.
           DISPLAY "STATUS MISMATCHES [RCN-102] : " WS-STAT-MISMATCH-CNT.
           DISPLAY "MISSING IN BANK [RCN-103]    : " WS-MISS-BANK-CNT.
           DISPLAY "MISSING IN MERCHANT [RCN-104]: " WS-MISS-MERCH-CNT.
           DISPLAY "TOTAL EXCEPTION RECORDS     : " WS-TOTAL-EXCP-CNT.
           DISPLAY "TOTAL DISCREPANCY AMOUNT    : $" WS-DISCREPANCY-TOTAL.
           DISPLAY "==================================================".
           IF WS-TOTAL-EXCP-CNT > 0
               MOVE 4 TO RETURN-CODE
               DISPLAY "FINAL STATUS: RC=04 (WARNING - EXCEPTIONS DETECTED)"
           ELSE
               MOVE 0 TO RETURN-CODE
               DISPLAY "FINAL STATUS: RC=00 (SUCCESS - PERFECT MATCH)"
           END-IF.

       4000-CLOSE-FILES.
           CLOSE BANK-FILE MERCH-FILE MATCH-FILE EXCP-FILE MISS-FILE.
