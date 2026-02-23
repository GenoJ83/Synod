import fitz  # PyMuPDF
from pptx import Presentation
import os

class ExtractorService:
    @staticmethod
    def extract_text(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                text = ExtractorService._extract_from_pdf(file_path)
            elif ext == '.pptx':
                text = ExtractorService._extract_from_pptx(file_path)
            elif ext == '.txt':
                text = ExtractorService._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
            
            return ExtractorService._sanitize_text(text)
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {file_path}: {str(e)}")

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Basic sanitization: clean excessive whitespace and control characters."""
        if not text:
            return ""
        # Remove control characters and non-printable characters
        text = "".join(char for char in text if char.isprintable() or char in "\n\r\t")
        # Normalize whitespace (replace multiple spaces/newlines with single ones)
        import re
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def _extract_from_pptx(file_path: str) -> str:
        text = ""
        prs = Presentation(file_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += (shape.text or "") + "\n"
        return text

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
