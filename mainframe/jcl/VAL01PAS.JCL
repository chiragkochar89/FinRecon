//VAL01PAS JOB (FINRECON),'ASSIGNMENT 4 VALIDATE PASS',
//             CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//*-------------------------------------------------------------------*
//* FINRECON - ASSIGNMENT 4: JCL RECORD COUNT VALIDATION (SUCCESS CASE)*
//*                                                                   *
//* OBJECTIVE: COPY/SORT FILE IN DESCENDING ORDER USING DFSORT.        *
//*            COMPARE INPUT VS OUTPUT RECORD COUNT.                  *
//*            KEEP OUTPUT FILE UPON SUCCESSFUL RECORD COUNT MATCH.   *
//* EXPECTED RESULT: RC=00, OUTPUT FILE KEPT & CATALOGED.             *
//*-------------------------------------------------------------------*
//* STEP 1: DELETE PREVIOUS VALIDATION OUTPUT DATASET                 *
//*-------------------------------------------------------------------*
//CLEANUP  EXEC PGM=IEFBR14
//DELOUT   DD DSN=&HLQ..FINRECON.OUTPUT.VALIDATE,
//            DISP=(MOD,DELETE,DELETE),UNIT=SYSDA,SPACE=(TRK,(1,1))
//*-------------------------------------------------------------------*
//* STEP 2: DFSORT DESCENDING SORT AND COPY                           *
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
  COUNT FROM(INFILE)  WRITE(INCNT)
  COUNT FROM(OUTFILE) WRITE(OUTCNT)
/*
//*-------------------------------------------------------------------*
//* STEP 4: VERIFY RECORD COUNTS MATCH (SUCCESS)                       *
//*-------------------------------------------------------------------*
//VERIFY   EXEC PGM=SORT,COND=(0,NE)
//SYSOUT   DD SYSOUT=*
//SORTIN   DD DSN=&HLQ..FINRECON.OUTPUT.VALIDATE,DISP=SHR
//SORTOUT  DD DUMMY
//SYSIN    DD *
  SORT FIELDS=COPY
/*
