import os
import uuid
import logging
from typing import Tuple, Optional
from pypdf import PdfReader
from docx import Document as DocxDocument
from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_DOC_EXTENSIONS = {".txt", ".pdf", ".docx"}

class DocumentService:
    @staticmethod
    def is_valid_document(filename: str, file_size: int) -> bool:
        """Validates document extension and size limit (15MB)."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_DOC_EXTENSIONS:
            return False
        if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            return False
        return True

    @staticmethod
    def get_safe_storage_path(filename: str) -> str:
        """Generates a secure, non-colliding server-side storage path."""
        ext = os.path.splitext(filename)[1].lower()
        safe_name = f"{uuid.uuid4()}{ext}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        return os.path.join(settings.UPLOAD_DIR, safe_name)

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extracts plain text from TXT, PDF, and DOCX files."""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        try:
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

            elif ext == ".pdf":
                reader = PdfReader(file_path)
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted:
                        lines = [line.strip() for line in extracted.splitlines() if line.strip()]
                        page_content = " ".join(lines)
                        pages_text.append(f"--- Page {idx + 1} ---\n{page_content}")
                text = "\n\n".join(pages_text)

            elif ext == ".docx":
                doc = DocxDocument(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                text = "\n\n".join(paragraphs)

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise ValueError(f"Failed to parse document: {str(e)}")

        return text.strip()

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 100) -> list[str]:
        """
        Splits extracted document text into overlapping chunks.
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # If not at the very end, try breaking at a newline or period
            if end < text_len:
                last_newline = chunk.rfind("\n")
                last_period = chunk.rfind(". ")
                break_point = max(last_newline, last_period)
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + len(chunk)

            clean_chunk = chunk.strip()
            if clean_chunk:
                chunks.append(clean_chunk)

            start = end - chunk_overlap
            if start >= text_len or len(chunk) <= chunk_overlap:
                break

        return chunks
