from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Party(BaseModel):
    name: str
    role: Optional[str] = None

class Signatory(BaseModel):
    name: str
    title: Optional[str] = None

class LiabilityCap(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None

class ExtractedFields(BaseModel):
    parties: List[Party] = []
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: Optional[str] = None
    confidentiality: Optional[str] = None
    indemnity: Optional[str] = None
    liability_cap: Optional[LiabilityCap] = None
    signatories: List[Signatory] = []

class Citation(BaseModel):
    document_id: str
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    text_snippet: str

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: Optional[float] = None

class AuditFinding(BaseModel):
    severity: str  # "high", "medium", "low"
    clause_type: str
    description: str
    evidence: str
    document_id: str
    page: Optional[int] = None
    recommendation: Optional[str] = None

class IngestResponse(BaseModel):
    document_ids: List[str]
    message: str
    processed_count: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str