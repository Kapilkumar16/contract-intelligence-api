import os
import json
from app.models import ExtractedFields, Party, Signatory, LiabilityCap

class ExtractionService:
    """Service for extracting structured fields from contracts using AI"""
    
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        
        if self.provider == "groq":
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"  # Fast and accurate
        else:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def extract_fields(self, document_text: str) -> ExtractedFields:
        """Extract structured fields from contract text"""
        
        prompt = f"""
You are a contract analysis expert. Extract the following information from the contract below.
Return ONLY a valid JSON object with these exact fields:

{{
  "parties": [
    {{"name": "Party Name", "role": "Buyer/Seller/etc"}}
  ],
  "effective_date": "date or null",
  "term": "contract duration or null",
  "governing_law": "jurisdiction or null",
  "payment_terms": "summary or null",
  "termination": "termination conditions or null",
  "auto_renewal": "auto-renewal terms or null",
  "confidentiality": "confidentiality terms or null",
  "indemnity": "indemnity terms or null",
  "liability_cap": {{"amount": number, "currency": "USD/EUR/etc"}},
  "signatories": [
    {{"name": "Signatory Name", "title": "Title"}}
  ]
}}

If any field is not found, use null or empty array [].

CONTRACT TEXT:
{document_text[:8000]}

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
            
           
            extracted_data = json.loads(response_text)
            
            
            return ExtractedFields(
                parties=[Party(**p) for p in extracted_data.get("parties", [])],
                effective_date=extracted_data.get("effective_date"),
                term=extracted_data.get("term"),
                governing_law=extracted_data.get("governing_law"),
                payment_terms=extracted_data.get("payment_terms"),
                termination=extracted_data.get("termination"),
                auto_renewal=extracted_data.get("auto_renewal"),
                confidentiality=extracted_data.get("confidentiality"),
                indemnity=extracted_data.get("indemnity"),
                liability_cap=LiabilityCap(**extracted_data["liability_cap"]) if extracted_data.get("liability_cap") else None,
                signatories=[Signatory(**s) for s in extracted_data.get("signatories", [])]
            )
        
        except json.JSONDecodeError as e:
            
            return ExtractedFields()
        except Exception as e:
            raise Exception(f"Extraction error: {str(e)}")