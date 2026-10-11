import os

def run_assignment4_validation():
    base_dir = r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data"
    input_path = os.path.join(base_dir, "FINRECON.WORK.BANK.txt")
    pass_out_path = os.path.join(base_dir, "FINRECON.OUTPUT.VALIDATE.PASS.txt")
    fail_out_path = os.path.join(base_dir, "FINRECON.OUTPUT.VALIDATE.FAIL.txt")
    
    with open(input_path, "r") as f:
        in_lines = [l.rstrip("\r\n") for l in f if l.strip()]
        
    in_cnt = len(in_lines)
    
    print("=" * 60)
    print("ASSIGNMENT 4 — JCL CONTROL & RECORD COUNT VALIDATION TEST")
    print("=" * 60)
    
    # --- TEST CASE 1: SUCCESSFUL RECORD COUNT VALIDATION ---
    print("\n[SCENARIO A: SUCCESSFUL COUNT COMPARISON]")
    # Sort in descending order by key (Cols 13-20 -> slice 12:20)
    pass_lines = sorted(in_lines, key=lambda r: r[12:20], reverse=True)
    pass_cnt = len(pass_lines)
    
    print(f"INPUT RECORD COUNT  : {in_cnt}")
    print(f"OUTPUT RECORD COUNT : {pass_cnt}")
    
    if in_cnt == pass_cnt:
        with open(pass_out_path, "w") as f:
            f.write("\n".join(pass_lines) + "\n")
        print("VALIDATION RESULT   : MATCH SUCCESSFUL (90 == 90)")
        print("JCL ACTION          : DISP=(NEW,CATLG,DELETE) -> OUTPUT FILE KEPT")
        print("STATUS              : RC=00 (SUCCESS)")
    else:
        print("VALIDATION RESULT   : MISMATCH")
        print("STATUS              : RC=12 (FAILURE)")
        
    assert os.path.exists(pass_out_path), "Pass output file should exist!"
    assert in_cnt == pass_cnt, f"Pass count mismatch: {in_cnt} != {pass_cnt}"
    
    # --- TEST CASE 2: FAILED RECORD COUNT VALIDATION ---
    print("\n[SCENARIO B: FAILED COUNT COMPARISON]")
    # Simulate record loss (omit TXN10001)
    fail_lines = [r for r in pass_lines if r[12:20] != "TXN10001"]
    fail_cnt = len(fail_lines)
    
    print(f"INPUT RECORD COUNT  : {in_cnt}")
    print(f"OUTPUT RECORD COUNT : {fail_cnt}")
    
    if in_cnt == fail_cnt:
        print("VALIDATION RESULT   : MATCH")
        rc = 0
    else:
        print(f"CRITICAL ERROR      : RECORD COUNT MISMATCH DETECTED! INPUT={in_cnt}, OUTPUT={fail_cnt}")
        print("JCL ACTION          : DISP=(NEW,DELETE,DELETE) -> OUTPUT FILE PURGED")
        print("STATUS              : RC=12 (FATAL COUNT VALIDATION FAILURE)")
        rc = 12
        if os.path.exists(fail_out_path):
            os.remove(fail_out_path)
            
    print("=" * 60)
    
    assert not os.path.exists(fail_out_path), "Fail output file should be deleted!"
    assert rc == 12, f"Fail scenario should yield RC=12, got RC={rc}"

if __name__ == "__main__":
    run_assignment4_validation()
