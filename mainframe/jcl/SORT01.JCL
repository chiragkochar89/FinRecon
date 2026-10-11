//SORT01   JOB (FINRECON),'ASSIGNMENT 1 DFSORT',
//             CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//*-------------------------------------------------------------------*
//* FINRECON - ASSIGNMENT 1: DFSORT DEDUPLICATION AND SORTING         *
//*                                                                   *
//* INPUT  : &HLQ.FINRECON.INPUT.BANK (100 RECS, 80 BYTES, RANDOM)    *
//* KEY    : COLUMNS 13-20 (8 BYTES, CHAR)                            *
//* OUTPUT : &HLQ.FINRECON.WORK.BANK  (90 RECS, 80 BYTES, SORTED)    *
//* STATS  : INPUT COUNT=100, DUPLICATES REMOVED=10, OUTPUT COUNT=90  *
//*-------------------------------------------------------------------*
//* STEP 1: DELETE PRE EXISTING WORK DATASET                          *
//*-------------------------------------------------------------------*
//DELWORK  EXEC PGM=IEFBR14
//WORKBANK DD DSN=&HLQ..FINRECON.WORK.BANK,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//*-------------------------------------------------------------------*
//* STEP 2: EXECUTE IBM DFSORT FOR DEDUPLICATION AND ASCENDING SORT  *
//*-------------------------------------------------------------------*
//SRTBANK  EXEC PGM=SORT
//SYSOUT   DD SYSOUT=*
//SORTIN   DD DSN=&HLQ..FINRECON.INPUT.BANK,DISP=SHR
//SORTOUT  DD DSN=&HLQ..FINRECON.WORK.BANK,
//            DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,5),RLSE),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=27920)
//SYSIN    DD *
  SORT FIELDS=(13,8,CH,A)
  SUM FIELDS=NONE
/*
//*-------------------------------------------------------------------*
//* STEP 3: ICETOOL AUDIT REPORTING FOR DEDUPLICATION STATISTICS      *
//*-------------------------------------------------------------------*
//STATSTEP EXEC PGM=ICETOOL
//TOOLMSG  DD SYSOUT=*
//DFSMSG   DD SYSOUT=*
//INFILE   DD DSN=&HLQ..FINRECON.INPUT.BANK,DISP=SHR
//OUTFILE  DD DSN=&HLQ..FINRECON.WORK.BANK,DISP=SHR
//TOOLIN   DD *
  COUNT FROM(INFILE)  
  COUNT FROM(OUTFILE) 
/*
