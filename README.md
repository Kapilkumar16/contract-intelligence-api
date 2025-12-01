# Contract Intelligence API

AI-powered contract analysis system for extracting structured data, answering questions, and detecting risky clauses in legal documents.

## 🚀 Features

- **Document Ingestion**: Upload and process multiple PDF contracts
- **Field Extraction**: Extract parties, dates, terms, liability caps, and signatories
- **Question Answering (RAG)**: Ask natural language questions about contracts
- **Risk Audit**: Automatically detect risky clauses (auto-renewal, liability, indemnity)
- **Streaming Responses**: Real-time answer streaming via SSE
- **Webhook Support**: Event notifications for long-running tasks
- **Dual AI Provider**: Support for both Gemini and Groq APIs
- **Rule-based Fallback**: Falls back to regex patterns when AI is unavailable

---

## 🏗️ Architecture

<img width="1219" height="1050" alt="diagram-export-30-11-2025-22_06_37" src="https://github.com/user-attachments/assets/e8b00b99-179b-44bf-935a-b269e1126a27" />



---

## 📋 Prerequisites

- Docker Desktop
- Python 3.9+ (for local development)
- API Key :
  - [Groq](https://console.groq.com/keys)

---

## 🔧 Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/Kapilkumar16/contract-intelligence-api.git
cd contract-intelligence-api
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
# Choose AI Provider: "groq"
AI_PROVIDER=groq

# Groq API (recommended - faster)
GROQ_API_KEY=your_groq_api_key_here


# Optional: Webhook URL for event notifications
WEBHOOK_URL=http://localhost:8080/webhook-receiver
```

### 3. Run with Docker

```bash
# Build and start
docker-compose up --build

# Or use Makefile
make up
```

API will be available at: **http://localhost:8000**

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

---

## 🎯 API Endpoints

### Document Management

#### Upload Documents
```bash
curl -X POST http://localhost:8000/ingest \
  -F "files=@contract.pdf"
```

**Response:**
```json
{
  "document_ids": ["abc123"],
  "message": "Successfully ingested 1 document(s)",
  "processed_count": 1
}
```

#### List Documents
```bash
curl http://localhost:8000/documents
```

---

### Extraction

#### Extract Structured Fields
```bash
curl -X POST "http://localhost:8000/extract?document_id=abc123"
```

**Response:**
```json
{
  "parties": [{"name": "Acme Corp", "role": "Buyer"}],
  "effective_date": "2024-01-15",
  "term": "12 months",
  "governing_law": "California",
  "liability_cap": {"amount": 100000, "currency": "USD"},
  "signatories": [{"name": "John Doe", "title": "CEO"}]
}
```

---

### Question Answering (RAG)

#### Ask Questions
```bash
curl -X POST "http://localhost:8000/ask?question=What%20are%20the%20payment%20terms?"
```

**Response:**
```json
{
  "answer": "Payment is due within 30 days of invoice date...",
  "citations": [
    {
      "document_id": "abc123",
      "page": 3,
      "text_snippet": "Payment terms: Net 30..."
    }
  ],
  "confidence": 0.85
}
```

#### Stream Answers (Real-time)
```bash
curl -N "http://localhost:8000/ask/stream?question=Summarize%20this%20contract"
```

---

### Risk Audit

#### Audit Contract
```bash
curl -X POST "http://localhost:8000/audit?document_id=abc123"
```

**Response:**
```json
[
  {
    "severity": "high",
    "clause_type": "auto_renewal",
    "description": "Auto-renewal with only 15 days notice",
    "evidence": "Contract renews automatically unless...",
    "recommendation": "Negotiate for 60-day notice period"
  }
]
```

---

### Admin

#### Health Check
```bash
curl http://localhost:8000/healthz
```

#### Metrics
```bash
curl http://localhost:8000/metrics
```

---

## 🧪 Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test
pytest tests/test_extraction.py -v
```

---

## 🔒 Security Features

- **PII Redaction**: Names, emails, and SSNs redacted in logs
- **API Key Protection**: Sensitive keys never logged
- **Input Validation**: All inputs validated via Pydantic
- **Rate Limiting**: Built-in rate limiting on endpoints
- **CORS**: Configurable CORS settings

---

## 🎨 Design Trade-offs

### 1. **In-Memory Storage vs Database**
- **Choice**: In-memory dictionary
- **Why**: Simpler for MVP, faster development
- **Trade-off**: Data lost on restart (production would use PostgreSQL)

### 2. **AI Provider Flexibility**
- **Choice**: Support both Gemini and Groq
- **Why**: Groq is faster, Gemini has better accuracy
- **Trade-off**: Slightly more complex code

### 3. **No Text Chunking**
- **Choice**: Send first 8000 chars to AI
- **Why**: Most contracts fit, simpler implementation
- **Trade-off**: Very large documents might lose context (see chunking section in design doc)

### 4. **Regex Fallback**
- **Choice**: Rule-based extraction when AI fails
- **Why**: Ensures system always returns something
- **Trade-off**: Lower accuracy but higher reliability

---

## 📊 Performance

- **Document Upload**: ~2-5 seconds per PDF
- **Extraction**: ~3-8 seconds (depends on AI provider)
- **Question Answering**: ~2-5 seconds
- **Audit**: ~5-10 seconds

---

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution**: Ensure `.env` file has API key without quotes

### Issue: PDF extraction fails
**Solution**: Ensure PDF is not password-protected or corrupted

### Issue: Slow responses
**Solution**: Switch to Groq API (faster than Gemini)

---

## 📁 Project Structure

```
contract-intelligence-api/
├── app/
│   ├── services/          # Business logic
│   ├── utils/            # Helper functions
│   ├── main.py           # FastAPI app
│   └── models.py         # Pydantic models
├── tests/                # Unit & integration tests
├── prompts/              # LLM prompts with rationale
├── eval/                 # Q&A evaluation set
├── uploads/              # PDF storage
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🚢 Production Considerations

For production deployment, consider:

1. **Database**: Replace in-memory store with PostgreSQL
2. **Vector Store**: Use Pinecone/Weaviate for better RAG
3. **Caching**: Add Redis for API response caching
4. **Queue**: Use Celery for async processing
5. **Monitoring**: Add Sentry/DataDog
6. **Security**: Add OAuth2/JWT authentication





## 🙏 Acknowledgments

- FastAPI for the excellent framework
- Google Gemini & Groq for AI capabilities
- PyPDF2 for PDF processing
