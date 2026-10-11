//RECON01  JOB (FINRECON),'ASSIGNMENT 2 COBOL RECON',
//             CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//*-------------------------------------------------------------------*
//* FINRECON - ASSIGNMENT 2: COBOL RECONCILIATION ENGINE              *
//*                                                                   *
//* INPUT 1 : &HLQ.FINRECON.WORK.BANK     (50 RECS, LRECL=80, KEY 13-20)*
//* INPUT 2 : &HLQ.FINRECON.WORK.MERCHANT (50 RECS, LRECL=80, KEY 21-28)*
//* OUTPUTS : &HLQ.FINRECON.OUTPUT.MATCHED   (MATCHED TRANSACTIONS)   *
//*           &HLQ.FINRECON.OUTPUT.EXCEPTION (AMT/STAT MISMATCHES)    *
//*           &HLQ.FINRECON.OUTPUT.MISSING   (MISSING IN BANK/MERCH)  *
//*-------------------------------------------------------------------*
//* STEP 1: DELETE PREVIOUS OUTPUT DATASETS                           *
//*-------------------------------------------------------------------*
//CLEANUP  EXEC PGM=IEFBR14
//DELMAT   DD DSN=&HLQ..FINRECON.OUTPUT.MATCHED,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//DELEXC   DD DSN=&HLQ..FINRECON.OUTPUT.EXCEPTION,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//DELMIS   DD DSN=&HLQ..FINRECON.OUTPUT.MISSING,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//*-------------------------------------------------------------------*
//* STEP 2: PRE-SORT MERCHANT FILE BY PRIMARY KEY (COLS 21-28)        *
//*-------------------------------------------------------------------*
//SRTMCH   EXEC PGM=SORT
//SYSOUT   DD SYSOUT=*
//SORTIN   DD DSN=&HLQ..FINRECON.INPUT.MERCHANT,DISP=SHR
//SORTOUT  DD DSN=&HLQ..FINRECON.WORK.MERCHANT,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=27920)
//SYSIN    DD *
  SORT FIELDS=(21,8,CH,A)
  SUM FIELDS=NONE
/*
//*-------------------------------------------------------------------*
//* STEP 3: EXECUTE COBOL RECONCILIATION ENGINE (FINREC01)            *
//*-------------------------------------------------------------------*
//RUNRECON EXEC PGM=FINREC01
//STEPLIB  DD DSN=&HLQ..FINRECON.LOAD,DISP=SHR
//BANKIN   DD DSN=&HLQ..FINRECON.WORK.BANK,DISP=SHR
//MERCHIN  DD DSN=&HLQ..FINRECON.WORK.MERCHANT,DISP=SHR
//MATCHOUT DD DSN=&HLQ..FINRECON.OUTPUT.MATCHED,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=27920)
//EXCPOUT  DD DSN=&HLQ..FINRECON.OUTPUT.EXCEPTION,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=27920)
//MISSOUT  DD DSN=&HLQ..FINRECON.OUTPUT.MISSING,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=27920)
//SYSOUT   DD SYSOUT=*
/*
