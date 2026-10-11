import os
from decimal import Decimal, InvalidOperation
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BankRecord:
    line_number: int
    acct_no: str
    transaction_id: str
    trxn_date: str
    trxn_time: str
    amount: Decimal
    curr_code: str
    trxn_type: str
    bank_status: str
    merch_id: str
    ref_no: str
    raw_line: str

@dataclass
class MerchantRecord:
    line_number: int
    merch_id: str
    acct_no: str
    transaction_id: str
    trxn_date: str
    trxn_time: str
    amount: Decimal
    curr_code: str
    trxn_type: str
    merchant_status: str
    ref_no: str
    raw_line: str

class FeedParserService:
    """
    Fixed-Width Feed Parser Service (Phase 7B):
    Parses bank and merchant fixed-width records (80 bytes per line) using exact Decimal precision.
    Validates field positions, record lengths, numeric formats, and statuses.
    """

    @staticmethod
    def parse_bank_file(file_path: str) -> Tuple[List[BankRecord], List[str]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Bank feed file not found at: {file_path}")

        records: List[BankRecord] = []
        errors: List[str] = []

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, 1):
                clean_line = line.strip("\r\n")
                if not clean_line:
                    continue

                if len(clean_line) != 80:
                    errors.append(f"FINRECON.INPUT.BANK.txt Line {idx}: Invalid record length ({len(clean_line)} != 80 chars)")
                    continue

                try:
                    acct_no = clean_line[0:12].strip()
                    transaction_id = clean_line[12:20].strip()
                    trxn_date = clean_line[20:28].strip()
                    trxn_time = clean_line[28:34].strip()
                    amt_str = clean_line[34:46].strip()
                    curr_code = clean_line[46:49].strip()
                    trxn_type = clean_line[49:51].strip()
                    bank_status = clean_line[51:53].strip()
                    merch_id = clean_line[53:61].strip()
                    ref_no = clean_line[61:76].strip()

                    if not transaction_id:
                        errors.append(f"FINRECON.INPUT.BANK.txt Line {idx}: Transaction ID cannot be blank")
                        continue

                    amt_cents = Decimal(amt_str)
                    amount = amt_cents / Decimal("100")

                    records.append(BankRecord(
                        line_number=idx,
                        acct_no=acct_no,
                        transaction_id=transaction_id,
                        trxn_date=trxn_date,
                        trxn_time=trxn_time,
                        amount=amount,
                        curr_code=curr_code,
                        trxn_type=trxn_type,
                        bank_status=bank_status,
                        merch_id=merch_id,
                        ref_no=ref_no,
                        raw_line=clean_line
                    ))
                except (InvalidOperation, ValueError) as e:
                    errors.append(f"FINRECON.INPUT.BANK.txt Line {idx}: Invalid numeric amount '{clean_line[34:46]}'")

        return records, errors

    @staticmethod
    def parse_merchant_file(file_path: str) -> Tuple[List[MerchantRecord], List[str]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Merchant feed file not found at: {file_path}")

        records: List[MerchantRecord] = []
        errors: List[str] = []

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, 1):
                clean_line = line.strip("\r\n")
                if not clean_line:
                    continue

                if len(clean_line) != 80:
                    errors.append(f"FINRECON.INPUT.MERCHANT.txt Line {idx}: Invalid record length ({len(clean_line)} != 80 chars)")
                    continue

                try:
                    merch_id = clean_line[0:8].strip()
                    acct_no = clean_line[8:20].strip()
                    transaction_id = clean_line[20:28].strip()
                    trxn_date = clean_line[28:36].strip()
                    trxn_time = clean_line[36:42].strip()
                    amt_str = clean_line[42:54].strip()
                    curr_code = clean_line[54:57].strip()
                    trxn_type = clean_line[57:59].strip()
                    merchant_status = clean_line[59:61].strip()
                    ref_no = clean_line[61:76].strip()

                    if not transaction_id:
                        errors.append(f"FINRECON.INPUT.MERCHANT.txt Line {idx}: Transaction ID cannot be blank")
                        continue

                    amt_cents = Decimal(amt_str)
                    amount = amt_cents / Decimal("100")

                    records.append(MerchantRecord(
                        line_number=idx,
                        merch_id=merch_id,
                        acct_no=acct_no,
                        transaction_id=transaction_id,
                        trxn_date=trxn_date,
                        trxn_time=trxn_time,
                        amount=amount,
                        curr_code=curr_code,
                        trxn_type=trxn_type,
                        merchant_status=merchant_status,
                        ref_no=ref_no,
                        raw_line=clean_line
                    ))
                except (InvalidOperation, ValueError) as e:
                    errors.append(f"FINRECON.INPUT.MERCHANT.txt Line {idx}: Invalid numeric amount '{clean_line[42:54]}'")

        return records, errors

feed_parser = FeedParserService()
