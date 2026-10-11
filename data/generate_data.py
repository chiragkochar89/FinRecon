import random
import os

def generate_bank_data():
    """
    Assignment 1 & 2 Bank Dataset:
    - 100 records, 80 bytes each
    - Primary Key in cols 13-20 (8 bytes)
    - 90 distinct keys (TXN10001 to TXN10090)
    - 10 duplicates (TXN10001 to TXN10010 appear twice) -> 100 total records
    """
    records = []
    
    # 90 distinct keys
    distinct_keys = [f"TXN{10000 + i:05d}" for i in range(1, 91)]
    # 10 duplicate keys
    duplicate_keys = distinct_keys[:10]
    
    all_keys = distinct_keys + duplicate_keys  # 100 keys total
    
    # Seed for deterministic generation
    random.seed(42)
    random.shuffle(all_keys)
    
    for key in all_keys:
        acct_no = f"ACC{100000000 + random.randint(1, 50):09d}" # 12 B
        trxn_id = key.ljust(8)                                  # 8 B (Cols 13-20)
        trxn_date = "20260920"                                  # 8 B
        trxn_time = f"{random.randint(10, 23):02d}{random.randint(10, 59):02d}{random.randint(10, 59):02d}" # 6 B
        
        # Base amount
        k_num = int(key[3:]) - 10000
        if 1 <= k_num <= 40:
            amt = "000000125050"  # $1250.50 for matched/test range
        else:
            amt = f"{random.randint(100, 9999) * 100:012d}"
            
        curr = "USD"                                             # 3 B
        trxn_type = "CR" if k_num % 2 == 0 else "DR"             # 2 B
        
        if 1 <= k_num <= 40:
            stat = "AP"
        else:
            stat = "AP" if k_num % 5 != 0 else "PE"             # 2 B
            
        merch_id = f"MCH{90000 + (k_num % 10):05d}"             # 8 B
        ref_no = f"REF{987654321000 + k_num:012d}"              # 15 B
        filler = "    "                                         # 4 B
        
        rec = f"{acct_no}{trxn_id}{trxn_date}{trxn_time}{amt}{curr}{trxn_type}{stat}{merch_id}{ref_no}{filler}"
        assert len(rec) == 80, f"Record length error: {len(rec)} != 80"
        records.append(rec)
        
    return records

def generate_merchant_data():
    """
    Assignment 2 File2 Merchant Dataset:
    - 50 records, 80 bytes each
    - Primary Key in cols 21-28 (8 bytes)
    - Keys designed for reconciliation testing against Bank File:
      * TXN10001 to TXN10030 (30 recs): Matched
      * TXN10031 to TXN10035 (5 recs): Amount Mismatch (Merchant has 000000150000 vs Bank 000000125050)
      * TXN10036 to TXN10040 (5 recs): Status Mismatch (Merchant has RJ vs Bank AP)
      * TXN10091 to TXN10100 (10 recs): Missing in Bank (Present in Merchant only)
    """
    records = []
    
    # Merchant keys
    mch_keys = [f"TXN{10000 + i:05d}" for i in range(1, 41)] + [f"TXN{10000 + i:05d}" for i in range(91, 101)]
    
    for key in mch_keys:
        k_num = int(key[3:]) - 10000
        merch_id = f"MCH{90000 + (k_num % 10):05d}"             # 8 B (Cols 1-8)
        acct_no = f"ACC{100000000 + (k_num % 50) + 1:09d}"       # 12 B (Cols 9-20)
        trxn_id = key.ljust(8)                                  # 8 B (Cols 21-28)
        trxn_date = "20260920"                                  # 8 B
        trxn_time = "143015"                                    # 6 B
        
        # Mismatch rules
        if 31 <= k_num <= 35:
            amt = "000000150000"  # $1500.00 (Amount Mismatch!)
        else:
            amt = "000000125050" if (1 <= k_num <= 30 or 36 <= k_num <= 40) else f"{k_num * 1000:012d}"
            
        curr = "USD"                                             # 3 B
        trxn_type = "CR" if k_num % 2 == 0 else "DR"             # 2 B
        
        if 36 <= k_num <= 40:
            stat = "RJ"  # Rejected in Merchant (Status Mismatch!)
        else:
            stat = "AP"                                          # 2 B
            
        term_ref = f"TRM{987654321000 + k_num:012d}"             # 15 B
        filler = "    "                                         # 4 B
        
        rec = f"{merch_id}{acct_no}{trxn_id}{trxn_date}{trxn_time}{amt}{curr}{trxn_type}{stat}{term_ref}{filler}"
        assert len(rec) == 80, f"Merchant Record length error: {len(rec)} != 80"
        records.append(rec)
        
    return records

def generate_audit_data():
    """
    Assignment 3 REXX Audit Dataset:
    - 120 records, 100 bytes each
    - Primary Key in cols 25-32 (8 bytes)
    - 105 distinct keys (TXN10001 to TXN10105)
    - 15 duplicates (TXN10001 to TXN10115 appear twice) -> 120 total records
    """
    records = []
    distinct_keys = [f"TXN{10000 + i:05d}" for i in range(1, 106)]
    duplicate_keys = distinct_keys[:15]
    all_keys = distinct_keys + duplicate_keys
    
    random.seed(123)
    random.shuffle(all_keys)
    
    for idx, key in enumerate(all_keys, 1):
        aud_log_id = f"AUD202609{idx:03d}"                      # 12 B
        acct_no = f"ACC10000{idx:04d}"                          # 12 B
        trxn_id = key.ljust(8)                                  # 8 B (Cols 25-32)
        aud_date = "20260920"                                   # 8 B
        aud_time = "180000"                                     # 6 B
        aud_amt = f"{idx * 500:012d}"                            # 12 B
        merch_id = f"MCH900{(idx % 10):02d}"                     # 8 B
        recon_cd = "MT"                                         # 2 B
        aud_ref = f"AUDREF{idx:09d}"                            # 15 B
        filler = " " * 17                                       # 17 B
        
        rec = f"{aud_log_id}{acct_no}{trxn_id}{aud_date}{aud_time}{aud_amt}{merch_id}{recon_cd}{aud_ref}{filler}"
        assert len(rec) == 100, f"Audit Record length error: {len(rec)} != 100"
        records.append(rec)
        
    return records

if __name__ == "__main__":
    base_dir = r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data"
    
    bank_recs = generate_bank_data()
    with open(os.path.join(base_dir, "FINRECON.INPUT.BANK.txt"), "w") as f:
        f.write("\n".join(bank_recs) + "\n")
        
    merch_recs = generate_merchant_data()
    with open(os.path.join(base_dir, "FINRECON.INPUT.MERCHANT.txt"), "w") as f:
        f.write("\n".join(merch_recs) + "\n")
        
    audit_recs = generate_audit_data()
    with open(os.path.join(base_dir, "FINRECON.INPUT.AUDIT.txt"), "w") as f:
        f.write("\n".join(audit_recs) + "\n")
        
    print(f"Generated Bank dataset: {len(bank_recs)} records (80B each)")
    print(f"Generated Merchant dataset: {len(merch_recs)} records (80B each)")
    print(f"Generated Audit dataset: {len(audit_recs)} records (100B each)")
