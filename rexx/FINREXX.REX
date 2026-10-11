/* REXX - FINREXX: ASSIGNMENT 3 AUDIT PROCESSOR & DEDUPLICATOR */
/* READS 120-REC PS DATASET (100 BYTES, KEY IN COLS 25-32)       */
/* REMOVES 15 DUPLICATES, SORTS 105 UNIQUE RECS, PRINTS SUMMARY  */

PARSE ARG indsn outdsn

IF indsn = "" THEN indsn = "FINRECON.INPUT.AUDIT"
IF outdsn = "" THEN outdsn = "FINRECON.WORK.AUDIT"

SAY "============================================================"
SAY "FINREXX — REXX AUDIT DATASET PROCESSOR (ASSIGNMENT 3)"
SAY "============================================================"
SAY "INPUT DATASET  : " || indsn
SAY "OUTPUT DATASET : " || outdsn
SAY "PRIMARY KEY    : COLUMNS 25-32 (LENGTH 8)"
SAY "------------------------------------------------------------"

/* EXECIO READ ALL RECORDS FROM INPUT DATASET */
"ALLOC FI(AUDIN) DA('"indsn"') SHR"
"EXECIO * DISKR AUDIN (STEM INREC. FINIS"
"FREE FI(AUDIN)"

input_cnt = INREC.0
SAY "READ " || input_cnt || " INPUT AUDIT RECORDS."

/* DEDUPLICATION BY PRIMARY KEY (COLS 25-32) */
seen. = 0
unique_cnt = 0
dup_cnt = 0

DO i = 1 TO input_cnt
  rec = INREC.i
  key = SUBSTR(rec, 25, 8)
  
  IF seen.key = 1 THEN DO
    dup_cnt = dup_cnt + 1
  END
  ELSE DO
    seen.key = 1
    unique_cnt = unique_cnt + 1
    OUTREC.unique_cnt = rec
    KEYS.unique_cnt = key
  END
END

OUTREC.0 = unique_cnt

/* IN-MEMORY BUBBLE/INSERTION SORT BY PRIMARY KEY */
DO i = 1 TO unique_cnt - 1
  DO j = i + 1 TO unique_cnt
    IF KEYS.i > KEYS.j THEN DO
      temp_key = KEYS.i
      KEYS.i = KEYS.j
      KEYS.j = temp_key
      
      temp_rec = OUTREC.i
      OUTREC.i = OUTREC.j
      OUTREC.j = temp_rec
    END
  END
END

/* EXECIO WRITE SORTED UNIQUE RECORDS TO OUTPUT DATASET */
"ALLOC FI(AUDOUT) DA('"outdsn"') OLD"
"EXECIO " || unique_cnt || " DISKW AUDOUT (STEM OUTREC. FINIS"
"FREE FI(AUDOUT)"

SAY "------------------------------------------------------------"
SAY "FINREXX PROCESSING SUMMARY:"
SAY "TOTAL INPUT RECORDS      : " || input_cnt
SAY "DUPLICATE RECORDS REMOVED: " || dup_cnt
SAY "UNIQUE RECORDS SORTED    : " || unique_cnt
SAY "OUTPUT RECORDS WRITTEN   : " || unique_cnt
SAY "------------------------------------------------------------"
SAY "REXX EXECUTION COMPLETED SUCCESSFULLY (RC=00)"
SAY "============================================================"

EXIT 0
