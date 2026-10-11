//REXX01   JOB (FINRECON),'ASSIGNMENT 3 REXX EXEC',
//             CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//*-------------------------------------------------------------------*
//* FINRECON - ASSIGNMENT 3: REXX AUDIT PROCESSOR                     *
//*                                                                   *
//* INPUT  : &HLQ.FINRECON.INPUT.AUDIT (120 RECS, 100 BYTES, RANDOM)   *
//* KEY    : COLUMNS 25-32 (8 BYTES, CHAR)                            *
//* OUTPUT : &HLQ.FINRECON.WORK.AUDIT  (105 RECS, 100 BYTES, SORTED)   *
//* STATS  : INPUT=120, DUPLICATES=15, UNIQUE=105, OUTPUT=105          *
//*-------------------------------------------------------------------*
//* STEP 1: PRE-ALLOCATE WORK DATASET                                 *
//*-------------------------------------------------------------------*
//ALLOC    EXEC PGM=IEFBR14
//WORKAUD  DD DSN=&HLQ..FINRECON.WORK.AUDIT,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//NEWWORK  DD DSN=&HLQ..FINRECON.WORK.AUDIT,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=100,BLKSIZE=27900)
//*-------------------------------------------------------------------*
//* STEP 2: EXECUTE REXX EXECUTION VIA TSO BATCH (IKJEFT01)           *
//*-------------------------------------------------------------------*
//RUNREXX  EXEC PGM=IKJEFT01,DYNAMNBR=30
//SYSPROC  DD DSN=&HLQ..FINRECON.REXX,DISP=SHR
//SYSTSPRT DD SYSOUT=*
//SYSTSIN  DD *
  %FINREXX &HLQ..FINRECON.INPUT.AUDIT &HLQ..FINRECON.WORK.AUDIT
/*
