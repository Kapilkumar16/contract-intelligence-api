from typing import Dict, List
import json
from datetime import datetime

class DocumentStore:
    """Simple in-memory document storage"""
    
    def __init__(self):
        self.documents: Dict[str, dict] = {}
        self.metrics = {
            "total_ingests": 0,
            "total_extractions": 0,
            "total_questions": 0,
            "total_audits": 0
        }
    
    def store_document(self, doc_id: str, filename: str, text: str, metadata: dict = None):
        """Store a document with its text and metadata"""
        self.documents[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "text": text,
            "metadata": metadata or {},
            "uploaded_at": datetime.now().isoformat(),
            "page_count": metadata.get("page_count", 0) if metadata else 0
        }
        self.metrics["total_ingests"] += 1
    
    def get_document(self, doc_id: str) -> dict:
        """Retrieve a document by ID"""
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> List[dict]:
        """Get all stored documents"""
        return list(self.documents.values())
    
    def document_exists(self, doc_id: str) -> bool:
        """Check if document exists"""
        return doc_id in self.documents
    
    def get_metrics(self) -> dict:
        """Get system metrics"""
        return {
            **self.metrics,
            "total_documents": len(self.documents)
        }
    
    def increment_metric(self, metric_name: str):
        """Increment a metric counter"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1


db = DocumentStore()