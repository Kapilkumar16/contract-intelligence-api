from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
import httpx
import asyncio

from app.models import (
    IngestResponse, ExtractedFields, AskResponse, 
    AuditFinding, HealthResponse
)
from app.services.pdf_service import PDFService
from app.services.extraction_service import ExtractionService
from app.services.rag_service import RAGService
from app.services.audit_service import AuditService
from app.utils.db import db


load_dotenv()


app = FastAPI(
    title="Contract Intelligence API",
    description="AI-powered contract analysis and intelligence system",
    version="1.0.0"
)


pdf_service = PDFService()
extraction_service = ExtractionService()
rag_service = RAGService()
audit_service = AuditService()


#  ENDPOINTS 

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Contract Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz"
    }


@app.post("/ingest", response_model=IngestResponse, tags=["Document Management"])
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Upload and ingest PDF contracts
    Returns document IDs for uploaded files
    """
    print(f"DEBUG: Received {len(files)} files")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    document_ids = []
    processed_count = 0
    errors = []
    
    for file in files:
        print(f"DEBUG: Processing file: {file.filename}")
       
        if not file.filename.endswith('.pdf'):
            print(f"DEBUG: Skipping non-PDF file: {file.filename}")
            errors.append(f"Skipped {file.filename} - not a PDF")
            continue
        
        try:
            print(f"DEBUG: Reading file content...")
           
            content = await file.read()
            print(f"DEBUG: File size: {len(content)} bytes")
            
            
            file_path = pdf_service.save_uploaded_file(content, file.filename)
            print(f"DEBUG: Saved to: {file_path}")
            
           
            text, page_count = pdf_service.extract_text_from_pdf(file_path)
            print(f"DEBUG: Extracted {page_count} pages, {len(text)} characters")
            
            
            doc_id = pdf_service.generate_document_id(file.filename, text)
            print(f"DEBUG: Generated doc_id: {doc_id}")
            
           
            db.store_document(
                doc_id=doc_id,
                filename=file.filename,
                text=text,
                metadata={"page_count": page_count}
            )
            print(f"DEBUG: Stored in database")
            
            document_ids.append(doc_id)
            processed_count += 1
        
        except Exception as e:
            error_msg = f"Error processing {file.filename}: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            errors.append(error_msg)
            continue
    
    if processed_count == 0:
        error_detail = "No valid PDF files processed"
        if errors:
            error_detail += f". Errors: {'; '.join(errors)}"
        raise HTTPException(status_code=400, detail=error_detail)
    
    response = IngestResponse(
        document_ids=document_ids,
        message=f"Successfully ingested {processed_count} document(s)",
        processed_count=processed_count
    )
    
    if errors:
        print(f"DEBUG: Errors occurred: {errors}")
    
    print(f"DEBUG: Returning response: {response}")
    return response


@app.post("/extract", response_model=ExtractedFields, tags=["Extraction"])
async def extract_fields(document_id: str):
    """
    Extract structured fields from a contract
    """
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.increment_metric("total_extractions")
    
    try:
        extracted = extraction_service.extract_fields(doc['text'])
        return extracted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/ask", response_model=AskResponse, tags=["Question Answering"])
async def ask_question(question: str, document_ids: Optional[List[str]] = None):
    """
    Ask questions about uploaded contracts (RAG)
    """
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    db.increment_metric("total_questions")
    
    try:
        response = rag_service.answer_question(question, document_ids)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")


@app.get("/ask/stream", tags=["Question Answering"])
async def ask_question_stream(question: str, document_ids: Optional[str] = None):
    """
    Stream answer tokens in real-time (SSE)
    """
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    
    doc_id_list = document_ids.split(',') if document_ids else None
    
    async def event_generator():
        for chunk in rag_service.answer_question_stream(question, doc_id_list):
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.01)
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.post("/audit", response_model=List[AuditFinding], tags=["Audit"])
async def audit_document(document_id: str):
    """
    Audit contract for risky clauses
    """
    if not db.document_exists(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.increment_metric("total_audits")
    
    try:
        findings = audit_service.audit_document(document_id)
        return findings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


async def send_webhook(url: str, data: dict):
    """Send webhook notification"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=data, timeout=5.0)
    except Exception as e:
        print(f"Webhook failed: {str(e)}")


@app.post("/webhook/events", tags=["Webhooks"])
async def trigger_webhook_event(
    background_tasks: BackgroundTasks,
    event_type: str,
    document_id: str,
    data: dict = None
):
    """
    Trigger webhook event (for long-running tasks)
    """
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return {"message": "Webhook URL not configured"}
    
    payload = {
        "event_type": event_type,
        "document_id": document_id,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    
    background_tasks.add_task(send_webhook, webhook_url, payload)
    
    return {"message": "Webhook event queued", "payload": payload}


@app.get("/healthz", response_model=HealthResponse, tags=["Admin"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/metrics", tags=["Admin"])
async def get_metrics():
    """Get system metrics"""
    return db.get_metrics()


@app.get("/documents", tags=["Document Management"])
async def list_documents():
    """List all uploaded documents"""
    docs = db.get_all_documents()
    return {
        "total": len(docs),
        "documents": [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "uploaded_at": doc["uploaded_at"],
                "page_count": doc.get("page_count", 0)
            }
            for doc in docs
        ]
    }








if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)