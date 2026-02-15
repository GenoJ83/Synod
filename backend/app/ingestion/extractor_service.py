import fitz  # PyMuPDF
from pptx import Presentation
import os

class ExtractorService:
    @staticmethod
    def extract_text(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return ExtractorService._extract_from_pdf(file_path)
        elif ext == '.pptx':
            return ExtractorService._extract_from_pptx(file_path)
        elif ext == '.txt':
            return ExtractorService._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

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
                    text += shape.text + "\n"
        return text

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
