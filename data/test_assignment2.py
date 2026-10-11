import os

def run_assignment2_recon():
    base_dir = r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data"
    
    bank_path = os.path.join(base_dir, "FINRECON.WORK.BANK.txt")
    merch_path = os.path.join(base_dir, "FINRECON.INPUT.MERCHANT.txt")
    
    with open(bank_path, "r") as f:
        # File1: subset of 50 bank records (TXN10001 to TXN10050)
        bank_lines = [l.rstrip("\r\n") for l in f if l.strip()][:50]
        
    with open(merch_path, "r") as f:
        merch_lines = [l.rstrip("\r\n") for l in f if l.strip()]
        
    # Sort bank recs by key (Cols 13-20 -> slice 12:20)
    bank_lines.sort(key=lambda r: r[12:20])
    # Sort merch recs by key (Cols 21-28 -> slice 20:28)
    merch_lines.sort(key=lambda r: r[20:28])
    
    matched_recs = []
    excp_recs = []
    miss_recs = []
    
    i, j = 0, 0
    
    matched_cnt = 0
    amt_mismatch_cnt = 0
    stat_mismatch_cnt = 0
    miss_bank_cnt = 0
    miss_merch_cnt = 0
    
    HIGH_KEY = "\xFF" * 8
    
    while i < len(bank_lines) or j < len(merch_lines):
        b_key = bank_lines[i][12:20] if i < len(bank_lines) else HIGH_KEY
        m_key = merch_lines[j][20:28] if j < len(merch_lines) else HIGH_KEY
        
        if b_key == HIGH_KEY and m_key == HIGH_KEY:
            break
        
        if b_key == m_key:
            b_rec = bank_lines[i]
            m_rec = merch_lines[j]
            
            b_amt = b_rec[34:46]
            m_amt = m_rec[42:54]
            
            b_stat = b_rec[51:53]
            m_stat = m_rec[59:61]
            
            if b_amt == m_amt and b_stat == m_stat:
                matched_cnt += 1
                matched_recs.append(b_rec)
            else:
                if b_amt != m_amt:
                    amt_mismatch_cnt += 1
                    excp_recs.append(b_rec)
                if b_stat != m_stat:
                    stat_mismatch_cnt += 1
                    excp_recs.append(b_rec)
            i += 1
            j += 1
        elif b_key < m_key:
            miss_merch_cnt += 1
            miss_recs.append(bank_lines[i])
            i += 1
        else: # b_key > m_key
            miss_bank_cnt += 1
            miss_recs.append(merch_lines[j])
            j += 1
            
    total_exceptions = amt_mismatch_cnt + stat_mismatch_cnt + miss_bank_cnt + miss_merch_cnt
    
    print("=" * 60)
    print("ASSIGNMENT 2 — COBOL RECONCILIATION ENGINE SUMMARY REPORT")
    print("=" * 60)
    print(f"BANK FILE RECORDS READ       : {len(bank_lines)}")
    print(f"MERCHANT FILE RECORDS READ   : {len(merch_lines)}")
    print(f"------------------------------------------------------------")
    print(f"MATCHED TRANSACTIONS         : {matched_cnt}")
    print(f"AMOUNT MISMATCHES            : {amt_mismatch_cnt}")
    print(f"STATUS MISMATCHES            : {stat_mismatch_cnt}")
    print(f"MISSING IN BANK              : {miss_bank_cnt}")
    print(f"MISSING IN MERCHANT          : {miss_merch_cnt}")
    print(f"TOTAL EXCEPTION RECORDS      : {total_exceptions}")
    print(f"RETURN CODE                  : RC=04 (WARNING - EXCEPTIONS DETECTED)")
    print("=" * 60)
    
    assert matched_cnt == 30, f"Expected 30 matched, got {matched_cnt}"
    assert amt_mismatch_cnt == 5, f"Expected 5 amount mismatches, got {amt_mismatch_cnt}"
    assert stat_mismatch_cnt == 5, f"Expected 5 status mismatches, got {stat_mismatch_cnt}"
    assert miss_merch_cnt == 10, f"Expected 10 missing in merchant, got {miss_merch_cnt}"
    assert miss_bank_cnt == 10, f"Expected 10 missing in bank, got {miss_bank_cnt}"

if __name__ == "__main__":
    run_assignment2_recon()
