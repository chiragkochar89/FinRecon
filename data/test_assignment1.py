import os

def run_assignment1_sort():
    base_dir = r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data"
    input_path = os.path.join(base_dir, "FINRECON.INPUT.BANK.txt")
    output_path = os.path.join(base_dir, "FINRECON.WORK.BANK.txt")
    
    with open(input_path, "r") as f:
        lines = [line.rstrip("\r\n") for line in f if line.strip()]
        
    input_count = len(lines)
    
    # DFSORT SUM FIELDS=NONE on Cols 13-20 (0-based slice 12:20)
    seen_keys = set()
    unique_records = []
    duplicate_count = 0
    
    # DFSORT processes and deduplicates based on first occurrence, then sorts by key
    for rec in lines:
        key = rec[12:20]
        if key in seen_keys:
            duplicate_count += 1
        else:
            seen_keys.add(key)
            unique_records.append(rec)
            
    # SORT FIELDS=(13,8,CH,A)
    sorted_records = sorted(unique_records, key=lambda x: x[12:20])
    output_count = len(sorted_records)
    
    with open(output_path, "w") as f:
        f.write("\n".join(sorted_records) + "\n")
        
    print("=" * 60)
    print("ASSIGNMENT 1 — DFSORT PROCESSING STATISTICS REPORT")
    print("=" * 60)
    print(f"INPUT DATASET           : FINRECON.INPUT.BANK")
    print(f"OUTPUT DATASET          : FINRECON.WORK.BANK")
    print(f"SORT KEY RANGE          : COLUMNS 13-20 (LENGTH 8)")
    print(f"TOTAL INPUT RECORDS     : {input_count}")
    print(f"DUPLICATE RECORDS REMOVED: {duplicate_count}")
    print(f"UNIQUE OUTPUT RECORDS   : {output_count}")
    print(f"SORT ORDER              : ASCENDING")
    print("STATUS                  : RC=00 (SUCCESSFUL DEDUPLICATION)")
    print("=" * 60)
    
    assert input_count == 100, f"Expected 100 input records, got {input_count}"
    assert duplicate_count == 10, f"Expected 10 duplicate records, got {duplicate_count}"
    assert output_count == 90, f"Expected 90 output records, got {output_count}"

if __name__ == "__main__":
    run_assignment1_sort()
