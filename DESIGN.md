# Contract Intelligence API - Design Document

## 1. System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Client Layer                         │
│              (Postman, Browser, cURL)                    │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌──────────────────────────────────────────────────────────┐
│                  FastAPI Application                     │
├──────────────────────────────────────────────────────────┤
│  Endpoints:                                              │
│  • POST /ingest      - Upload PDFs                       │
│  • POST /extract     - Extract fields                    │
│  • POST /ask         - Q&A (RAG)                         │
│  • GET /ask/stream   - Streaming Q&A                     │
│  • POST /audit       - Risk detection                    │
│  • GET /healthz      - Health check                      │
│  • GET /metrics      - Usage stats                       │
└────────────┬──────────────────┬──────────────────────────┘
             │                  │
             ▼                  ▼
┌─────────────────────┐  ┌──────────────────────┐
│   Service Layer     │  │   Storage Layer      │
├─────────────────────┤  ├──────────────────────┤
│ • PDFService        │  │ • DocumentStore      │
│ • ExtractionService │  │   (In-Memory Dict)   │
│ • RAGService        │  │ • Metadata           │
│ • AuditService      │  │ • Full Text          │
└──────┬──────────────┘  └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│           External AI Providers                 │
├─────────────────────────────────────────────────┤
│              │
│ • Groq API (groq SDK)                           │
│                                                  │
│ Fallback: Rule-based Regex Extraction           │
└─────────────────────────────────────────────────┘
```

---

## 2. Data Model

### Document Storage Schema

```python
Document {
    id: str              # MD5 hash of filename + content
    filename: str        # Original filename
    text: str            # Extracted text with [PAGE N] markers
    metadata: {
        page_count: int,
        uploaded_at: datetime,
        file_size: int
    },
    uploaded_at: datetime
}
```

### Extracted Fields Model

```python
ExtractedFields {
    parties: List[Party]           # Contract parties
    effective_date: str            # Start date
    term: str                      # Contract duration
    governing_law: str             # Jurisdiction
    payment_terms: str             # Payment details
    termination: str               # Exit conditions
    auto_renewal: str              # Renewal terms
    confidentiality: str           # NDA terms
    indemnity: str                 # Liability protection
    liability_cap: {               # Damage limits
        amount: float,
        currency: str
    },
    signatories: List[Signatory]   # Authorized signers
}
```

### Audit Finding Model

```python
AuditFinding {
    severity: str          # "high" | "medium" | "low"
    clause_type: str       # Type of risk
    description: str       # Risk explanation
    evidence: str          # Exact clause text
    document_id: str       # Source document
    page: int              # Location (optional)
    recommendation: str    # Mitigation advice
}
```

---

## 3. Text Processing & Chunking Rationale

### Current Approach: Simple Truncation

**Implementation:**
- Extract full text from PDF using PyPDF2
- Add `[PAGE N]` markers for citation tracking
- Send first 8,000 characters to AI models

**Rationale:**
1. **Speed**: No chunking overhead, single API call
2. **Simplicity**: Easier to implement and debug
3. **Coverage**: Most contracts are 5-15 pages (~6,000-18,000 chars)
4. **Cost**: Fewer API calls = lower cost

**Trade-offs:**
- ✅ Fast processing (2-5 seconds)
- ✅ Simple implementation
- ❌ Large documents (>20 pages) lose tail content
- ❌ No semantic chunking

### Alternative: Semantic Chunking (Future Enhancement)

**For production, consider:**

```python
# Pseudo-code for chunking strategy
def chunk_document(text, chunk_size=1000, overlap=200):
    """
    Strategy: Sliding window with overlap
    - Chunk size: 1000 tokens (~750 words)
    - Overlap: 200 tokens (preserves context)
    - Split on paragraph boundaries
    """
    chunks = []
    sentences = split_by_sentence(text)
    
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = count_tokens(sentence)
        
        if current_size + sentence_size > chunk_size:
            chunks.append(" ".join(current_chunk))
            # Keep last N sentences for overlap
            current_chunk = current_chunk[-3:]
            current_size = sum(count_tokens(s) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    return chunks
```

**Why not implemented yet:**
1. Adds 2-3 seconds processing time
2. Requires vector embeddings for retrieval
3. Increases complexity significantly
4. MVP doesn't need it for typical contracts

---

## 4. RAG (Retrieval-Augmented Generation) Strategy

### Current Implementation: Simple Context Injection

```
Query Flow:
1. User asks question
2. Retrieve all uploaded documents (or specified subset)
3. Concatenate documents with markers
4. Build prompt: QUESTION + DOCUMENTS + INSTRUCTIONS
5. Send to AI model
6. Parse response + extract citations
```

**Prompt Structure:**
```
Answer the following question based ONLY on the provided documents.

QUESTION: {user_question}

DOCUMENTS:
[DOCUMENT: doc_id_1]
{document_text}

[DOCUMENT: doc_id_2]
{document_text}

Provide answer with citations.
```

### Enhanced RAG (Future)

For better performance with many documents:

```python
# Vector-based retrieval
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# 1. Index documents
doc_embeddings = model.encode(document_chunks)

# 2. Embed query
query_embedding = model.encode(user_question)

# 3. Find top-K similar chunks
similarities = cosine_similarity(query_embedding, doc_embeddings)
top_chunks = get_top_k(similarities, k=5)

# 4. Use only relevant chunks in prompt
```

**Benefits:**
- Only relevant chunks sent to AI (lower cost)
- Better for large document sets (100+)
- More accurate citations

**Trade-offs:**
- Requires vector DB (Pinecone, Weaviate, ChromaDB)
- Adds infrastructure complexity
- Slower initial indexing

---

## 5. Fallback Behavior

### AI Provider Fallback Chain

```
Primary: User-selected AI (Gemini or Groq)
    ↓ [on failure]
Fallback Level 1: Rule-based Regex Extraction
    ↓ [on failure]
Fallback Level 2: Return empty structure with error flag
```

### Rule-based Extraction Patterns

```python
PATTERNS = {
    'date': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
    'money': r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
    'parties': r'(?:between|by and between)\s+([A-Z][^,]+)\s+(?:and|&)\s+([A-Z][^,]+)',
    'governing_law': r'governed by.*?laws of\s+([A-Za-z\s]+)',
    'term': r'term of\s+(\d+)\s+(year|month|day)s?',
}
```

**When Triggered:**
- AI API timeout (>30 seconds)
- API key invalid
- Rate limit exceeded
- Model unavailable (404/503 errors)

**Response Behavior:**
```json
{
  "parties": [...],  // From regex if found
  "extraction_method": "fallback_regex",
  "confidence": 0.4,
  "warning": "AI extraction failed, using pattern matching"
}
```

---

## 6. Security Considerations

### PII Redaction in Logs

```python
import re

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'name': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Simple name pattern
}

def redact_pii(text: str) -> str:
    for pattern_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f'[REDACTED_{pattern_type.upper()}]', text)
    return text
```

**Applied to:**
- All log messages
- Error responses
- Metrics endpoints
- Debug outputs

### API Key Protection

- Keys stored in `.env` (never in code)
- `.env` in `.gitignore`
- Keys loaded via `python-dotenv`
- Never logged or returned in responses

### Input Validation

- File type validation (PDF only)
- File size limits (10MB max)
- Document ID validation (alphanumeric only)
- Query sanitization (prevent injection)

### Rate Limiting

```python
from fastapi_limiter import FastAPILimiter

@app.post("/extract")
@limiter.limit("10/minute")  # 10 requests per minute
async def extract_fields(...):
    ...
```

---

## 7. Performance Optimization

### Current Optimizations

1. **In-Memory Storage**: Fast reads, no DB latency
2. **Async I/O**: FastAPI async endpoints
3. **Streaming Responses**: SSE for real-time Q&A
4. **Minimal Dependencies**: Small Docker image

### Future Optimizations

1. **Caching**: Redis for repeated queries
2. **Background Jobs**: Celery for long extraction tasks
3. **CDN**: CloudFront for static content
4. **Load Balancing**: Multiple API instances

---

## 8. Monitoring & Observability

### Metrics Collected

```python
{
    "total_ingests": 156,
    "total_extractions": 203,
    "total_questions": 847,
    "total_audits": 92,
    "total_documents": 156,
    "avg_response_time_ms": 3420,
    "error_rate": 0.02
}
```

### Logging Strategy

- **INFO**: Normal operations (upload, extract)
- **WARNING**: Fallback triggered, slow responses
- **ERROR**: AI failures, invalid requests
- **DEBUG**: Full prompts, responses (dev only)

---

## 9. Testing Strategy

### Test Pyramid

```
         ┌───────────┐
         │    E2E    │  ← Full workflow tests
         │  (5 tests)│
      ┌──┴───────────┴──┐
      │   Integration   │  ← API endpoint tests
      │   (20 tests)    │
   ┌──┴─────────────────┴──┐
   │      Unit Tests       │  ← Individual functions
   │      (50 tests)       │
   └───────────────────────┘
```

### Key Test Cases

1. **PDF Extraction**: Corrupted, encrypted, large files
2. **Field Extraction**: Missing fields, unusual formats
3. **Q&A Accuracy**: Measured with eval set (see eval/)
4. **Audit Detection**: Known risky clauses
5. **Fallback**: AI failure scenarios

---

## 10. Deployment Architecture

### Docker Compose (Development)

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - AI_PROVIDER=groq
```

### Production (AWS Example)

```
┌─────────────┐
│     ALB     │  (Load Balancer)
└──────┬──────┘
       │
   ┌───┴───┐
   │  ECS  │  (Container Service)
   │ Tasks │  (3+ replicas)
   └───┬───┘
       │
   ┌───┴───┐
   │  RDS  │  (PostgreSQL)
   └───────┘
```

**Services:**
- ALB: Route traffic, SSL termination
- ECS: Run Docker containers
- RDS: Persistent document storage
- S3: PDF file storage
- CloudWatch: Logging & metrics

---

## Summary

This design prioritizes **simplicity and speed** for MVP while maintaining **extensibility** for production scaling. Key decisions:

1. **In-memory storage**: Fast but ephemeral (trade-off accepted for MVP)
2. **Simple text truncation**: No chunking overhead (works for 95% of contracts)
3. **Dual AI support**: Flexibility in provider choice
4. **Rule-based fallback**: Ensures reliability over pure accuracy
5. **Security-first logging**: PII redaction built-in

Future enhancements would focus on vector-based RAG, persistent storage, and horizontal scaling.
