import os
import re
from app.models import AskResponse, Citation
from app.utils.db import db

class RAGService:
    """Retrieval-Augmented Generation service for Q&A"""
    
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
    
    def answer_question(self, question: str, document_ids: list = None) -> AskResponse:
        """Answer question based on uploaded documents"""
        
        # Get relevant documents
        if document_ids:
            docs = [db.get_document(doc_id) for doc_id in document_ids if db.document_exists(doc_id)]
        else:
            docs = db.get_all_documents()
        
        if not docs:
            return AskResponse(
                answer="No documents found. Please upload documents first.",
                citations=[]
            )
        
        # Build context from documents
        context = ""
        for doc in docs:
            context += f"\n\n[DOCUMENT: {doc['id']}]\n{doc['text'][:5000]}\n"
        
        prompt = f"""
Answer the following question based ONLY on the provided contract documents.
Include specific references to document sections when possible.

QUESTION: {question}

DOCUMENTS:
{context}

Provide a clear, accurate answer with citations. If the answer is not in the documents, say so.

ANSWER:
"""
        
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000
                )
                answer_text = response.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(prompt)
                answer_text = response.text.strip()
            
            
            citations = self._extract_citations(answer_text, docs)
            
            return AskResponse(
                answer=answer_text,
                citations=citations,
                confidence=0.85
            )
        
        except Exception as e:
            return AskResponse(
                answer=f"Error processing question: {str(e)}",
                citations=[]
            )
    
    def answer_question_stream(self, question: str, document_ids: list = None):
        """Stream answer tokens for real-time response"""
        
      
        if document_ids:
            docs = [db.get_document(doc_id) for doc_id in document_ids if db.document_exists(doc_id)]
        else:
            docs = db.get_all_documents()
        
        if not docs:
            yield "No documents found. Please upload documents first."
            return
        
        # Build context
        context = ""
        for doc in docs:
            context += f"\n\n[DOCUMENT: {doc['id']}]\n{doc['text'][:5000]}\n"
        
        prompt = f"""
Answer the following question based ONLY on the provided contract documents.

QUESTION: {question}

DOCUMENTS:
{context}

ANSWER:
"""
        
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000,
                    stream=True
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                response = self.model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
        
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _extract_citations(self, answer: str, docs: list) -> list:
        """Extract citations from answer text"""
        citations = []
        
        for doc in docs:
            doc_id = doc['id']
          
            page_pattern = r'\[PAGE (\d+)\]'
            pages = re.findall(page_pattern, doc['text'])
            
           
            if doc_id in answer or doc['filename'] in answer:
                citations.append(Citation(
                    document_id=doc_id,
                    page=int(pages[0]) if pages else None,
                    text_snippet=doc['text'][:200]
                ))
        
        return citations