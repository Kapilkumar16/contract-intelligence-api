import PyPDF2
import os
from typing import Tuple
import hashlib

class PDFService:
    """Service for PDF processing"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int]:
        """
        Extract text from PDF file
        Returns: (text_content, page_count)
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    # Add page markers for citation tracking
                    text += f"\n[PAGE {page_num + 1}]\n{page_text}\n"
            
            return text.strip(), page_count
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def generate_document_id(filename: str, content: str) -> str:
        """Generate unique document ID based on filename and content"""
        hash_input = f"{filename}_{content[:1000]}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    @staticmethod
    def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str = "uploads") -> str:
        """Save uploaded file to disk"""
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path