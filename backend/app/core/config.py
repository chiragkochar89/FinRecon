import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "FinRecon — Financial Transaction Processing & Automated Reconciliation Platform"
    VERSION: str = "2.0.0"
    FINRECON_MODE: str = os.getenv("FINRECON_MODE", "LOCAL_DEMO")  # LOCAL_DEMO or REAL_MAINFRAME
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DATA_DIRECTORY: str = os.getenv("DATA_DIRECTORY", r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    REPORT_DIRECTORY: str = os.getenv("REPORT_DIRECTORY", r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\reports")
    
    # Phase 3 Financial Control Thresholds
    HIGH_DISCREPANCY_THRESHOLD: float = float(os.getenv("HIGH_DISCREPANCY_THRESHOLD", "1000.00"))
    CONTROL_TOTAL_TOLERANCE: float = float(os.getenv("CONTROL_TOTAL_TOLERANCE", "0.00"))

settings = Settings()
