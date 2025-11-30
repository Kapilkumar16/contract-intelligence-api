import os
import json
from app.models import AuditFinding
from app.utils.db import db

class AuditService:
    """Service for auditing contracts and detecting risky clauses"""
    
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        
        if self.provider == "groq":
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
        else:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def audit_document(self, document_id: str) -> list:
        """Audit a document for risky clauses"""
        
        doc = db.get_document(document_id)
        if not doc:
            return []
        
        prompt = f"""
You are a legal contract auditor. Analyze this contract for risky clauses.

RISK CATEGORIES TO CHECK:
1. Auto-renewal with less than 30 days notice
2. Unlimited liability or no liability cap
3. Broad indemnity clauses
4. One-sided termination rights
5. Unfavorable payment terms
6. Lack of confidentiality protections
7. Unclear dispute resolution

For each risk found, return a JSON array with this structure:
[
  {{
    "severity": "high|medium|low",
    "clause_type": "auto_renewal|liability|indemnity|termination|payment|confidentiality|other",
    "description": "Brief description of the risk",
    "evidence": "Exact quote from contract (keep it short)",
    "recommendation": "How to mitigate this risk"
  }}
]

CONTRACT TEXT:
{doc['text'][:8000]}

Return ONLY the JSON array, no other text.

JSON OUTPUT:
"""
        
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
            
            
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
           
            findings_data = json.loads(response_text)
            
            
            findings = []
            for finding in findings_data:
                findings.append(AuditFinding(
                    severity=finding.get("severity", "low"),
                    clause_type=finding.get("clause_type", "other"),
                    description=finding.get("description", ""),
                    evidence=finding.get("evidence", ""),
                    document_id=document_id,
                    recommendation=finding.get("recommendation")
                ))
            
            return findings
        
        except json.JSONDecodeError:
            
            return [AuditFinding(
                severity="low",
                clause_type="other",
                description="Unable to complete full audit analysis",
                evidence="Analysis incomplete",
                document_id=document_id,
                recommendation="Manual review recommended"
            )]
        except Exception as e:
            return [AuditFinding(
                severity="low",
                clause_type="other",
                description=f"Audit error: {str(e)}",
                evidence="",
                document_id=document_id
            )]
    
    def batch_audit(self, document_ids: list) -> dict:
        """Audit multiple documents"""
        results = {}
        for doc_id in document_ids:
            if db.document_exists(doc_id):
                results[doc_id] = self.audit_document(doc_id)
        return results