from pydantic import BaseModel
from typing import List
from .verification_model import VerificationResult

class FinalReport(BaseModel):
    overall_score: int
    summary: str
    results: List[VerificationResult]