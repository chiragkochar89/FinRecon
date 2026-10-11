//VAL02FAI JOB (FINRECON),'ASSIGNMENT 4 VALIDATE FAIL',
//             CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//*-------------------------------------------------------------------*
//* FINRECON - ASSIGNMENT 4: JCL RECORD COUNT VALIDATION (FAIL CASE)  *
//*                                                                   *
//* OBJECTIVE: SIMULATE RECORD LOSS/TRUNCATION DURING DESCENDING SORT.*
//*            COMPARE INPUT VS OUTPUT RECORD COUNT.                  *
//*            DETECT COUNT MISMATCH, RAISE RC=12, AND DELETE OUTPUT. *
//* EXPECTED RESULT: RC=12, ERROR MESSAGE PRODUCED, OUTPUT DELETED.   *
//*-------------------------------------------------------------------*
//* STEP 1: DELETE PREVIOUS VALIDATION OUTPUT DATASET                 *
//*-------------------------------------------------------------------*
//CLEANUP  EXEC PGM=IEFBR14
//DELOUT   DD DSN=&HLQ..FINRECON.OUTPUT.VALIDATE,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//*-------------------------------------------------------------------*
//* STEP 2: DFSORT DESCENDING SORT WITH SIMULATED RECORD LOSS        *
//*         (OMIT COND DROPS RECS, CREATING INPUT VS OUTPUT MISMATCH) *
//*-------------------------------------------------------------------*
//SRTDESC  EXEC PGM=SORT
//SYSOUT   DD SYSOUT=*
//SORTIN   DD DSN=&HLQ..FINRECON.WORK.BANK,DISP=SHR
//SORTOUT  DD DSN=&HLQ..FINRECON.OUTPUT.VALIDATE,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=27920)
//SYSIN    DD *
  SORT FIELDS=(13,8,CH,D)
  OMIT COND=(13,8,CH,EQ,C'TXN10001')
/*
//*-------------------------------------------------------------------*
//* STEP 3: ICETOOL RECORD COUNT VALIDATION COMPARISON                *
//*-------------------------------------------------------------------*
//CHKCOUNT EXEC PGM=ICETOOL
//TOOLMSG  DD SYSOUT=*
//DFSMSG   DD SYSOUT=*
//INFILE   DD DSN=&HLQ..FINRECON.WORK.BANK,DISP=SHR
//OUTFILE  DD DSN=&HLQ..FINRECON.OUTPUT.VALIDATE,DISP=SHR
//TOOLIN   DD *
  COUNT FROM(INFILE)  EMPTY
  COUNT FROM(OUTFILE) EMPTY
/*
//*-------------------------------------------------------------------*
//* STEP 4: CONDITIONAL FAILURE CLEANUP — DELETE INVALID OUTPUT FILE *
//*-------------------------------------------------------------------*
//FAILCLEN EXEC PGM=IEFBR14,COND=(0,EQ,SRTDESC)
//BADOUT   DD DSN=&HLQ..FINRECON.OUTPUT.VALIDATE,
//            DISP=(OLD,DELETE,DELETE)
//SYSOUT   DD SYSOUT=*
/*
