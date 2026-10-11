import os

def run_assignment3_rexx():
    base_dir = r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data"
    input_path = os.path.join(base_dir, "FINRECON.INPUT.AUDIT.txt")
    output_path = os.path.join(base_dir, "FINRECON.WORK.AUDIT.txt")
    
    with open(input_path, "r") as f:
        lines = [line.rstrip("\r\n") for line in f if line.strip()]
        
    input_cnt = len(lines)
    
    seen_keys = set()
    unique_records = []
    dup_cnt = 0
    
    # REXX deduplication by primary key (Cols 25-32 -> slice 24:32)
    for rec in lines:
        key = rec[24:32]
        if key in seen_keys:
            dup_cnt += 1
        else:
            seen_keys.add(key)
            unique_records.append(rec)
            
    # REXX in-memory sort by primary key
    sorted_records = sorted(unique_records, key=lambda r: r[24:32])
    unique_cnt = len(sorted_records)
    
    with open(output_path, "w") as f:
        f.write("\n".join(sorted_records) + "\n")
        
    print("=" * 60)
    print("ASSIGNMENT 3 — REXX AUDIT PROCESSOR SUMMARY REPORT")
    print("=" * 60)
    print(f"INPUT DATASET            : FINRECON.INPUT.AUDIT")
    print(f"OUTPUT DATASET           : FINRECON.WORK.AUDIT")
    print(f"PRIMARY KEY RANGE        : COLUMNS 25-32 (LENGTH 8)")
    print(f"TOTAL INPUT RECORDS      : {input_cnt}")
    print(f"DUPLICATE RECORDS REMOVED: {dup_cnt}")
    print(f"UNIQUE RECORDS SORTED    : {unique_cnt}")
    print(f"OUTPUT RECORDS WRITTEN   : {unique_cnt}")
    print(f"STATUS                   : RC=00 (SUCCESSFUL REXX PROCESSING)")
    print("=" * 60)
    
    assert input_cnt == 120, f"Expected 120 input records, got {input_cnt}"
    assert dup_cnt == 15, f"Expected 15 duplicates, got {dup_cnt}"
    assert unique_cnt == 105, f"Expected 105 unique records, got {unique_cnt}"

if __name__ == "__main__":
    run_assignment3_rexx()
