# Extraction Prompt

## Prompt Template

```
You are a contract analysis expert. Extract the following information from the contract below.
Return ONLY a valid JSON object with these exact fields:

{
  "parties": [
    {"name": "Party Name", "role": "Buyer/Seller/etc"}
  ],
  "effective_date": "date or null",
  "term": "contract duration or null",
  "governing_law": "jurisdiction or null",
  "payment_terms": "summary or null",
  "termination": "termination conditions or null",
  "auto_renewal": "auto-renewal terms or null",
  "confidentiality": "confidentiality terms or null",
  "indemnity": "indemnity terms or null",
  "liability_cap": {"amount": number, "currency": "USD/EUR/etc"},
  "signatories": [
    {"name": "Signatory Name", "title": "Title"}
  ]
}

If any field is not found, use null or empty array [].

CONTRACT TEXT:
{document_text}

JSON OUTPUT:
```

## Rationale

**Why this prompt structure:**

1. **Clear Role**: "You are a contract analysis expert" - sets context for specialized task
2. **Explicit Output Format**: Shows exact JSON structure to reduce parsing errors
3. **Null Handling**: Instructs model what to do with missing fields (prevents hallucination)
4. **Structured Data**: JSON format allows easy parsing and validation

**Design Decisions:**

- **Temperature**: 0.1 (low creativity, high consistency)
- **Max Tokens**: 2000 (sufficient for structured output)
- **One-shot**: No examples needed; clear instructions work better

**Common Issues Fixed:**

- Added "ONLY" to prevent preambles like "Here's the extracted data..."
- Explicit "JSON OUTPUT:" marker helps model understand format requirement
- Field descriptions in placeholder values guide model interpretation

**Alternatives Considered:**

1. **Few-shot with examples**: Rejected - increases token usage without accuracy gain
2. **Chain-of-thought**: Rejected - unnecessary for structured extraction
3. **Function calling**: Considered but JSON parsing is simpler across providers