import fitz  # PyMuPDF
from pptx import Presentation
import os
import re

# Patterns for academic paper noise (appendices, figure OCR, citations)
_ARXIV_PATTERN = re.compile(
    r"arXiv:\d+\.\d+(?:v\d+)?\s*\[[\w.]+\]\s*\d+\s+\w+\s+\d{4}",
    re.IGNORECASE
)
# Common QA/prompt template leakage from paper appendices
_QA_PROMPT_PATTERNS = [
    re.compile(r"You have access to memories from[^.]+\.", re.IGNORECASE | re.DOTALL),
    re.compile(r"The answer should be (?:less than|at most) \d+[-–]?\d*\s*words?", re.IGNORECASE),
    re.compile(r"Answer the following question based on[^.]+\.", re.IGNORECASE),
    re.compile(r"\.\s*You have \d+ memories[^.]+\.", re.IGNORECASE | re.DOTALL),
]
# Reference-like lines (author et al., year - common in references section)
_REF_LINE = re.compile(
    r"^[\w\s,.-]+\set\s+al\.\s*[,.]?\s*\d{4}",
    re.IGNORECASE
)
# Figure/Table caption noise (short lines that are likely OCR from figures)
_CAPTION_NOISE = re.compile(
    r"^(?:Figure|Table|Fig\.|Tab\.)\s*\d*[.:]?\s*$",
    re.IGNORECASE
)


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
            
            text = ExtractorService._sanitize_text(text)
            # Extra cleanup for PDFs: strip academic paper noise (figures, appendices, refs)
            if ext == '.pdf':
                text = ExtractorService._clean_academic_noise(text)
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {file_path}: {str(e)}")

    @staticmethod
    def _clean_academic_noise(text: str) -> str:
        """Remove common academic paper noise: arXiv IDs, QA prompts, figure OCR, reference blocks."""
        if not text or len(text.strip()) < 100:
            return text

        # 1. Aggressive Header Stripping (Title, Authors, Emails, Affiliations)
        # Usually these are the first 10-20 lines of a paper
        lines = text.splitlines()
        content_start_idx = 0
        header_patterns = [
            re.compile(r"\{?[\w.-]+@[\w.-]+\}?"), # Emails
            re.compile(r"(?:University|Institute|Department|Laboratory|School|College|Academy|Faculty of)", re.IGNORECASE), # Affiliations
            re.compile(r"^\d+(?:st|nd|rd|th)?\s+(?:Author|Writer|Contributor)$", re.IGNORECASE),
            re.compile(r"^\*?\s*Corresponding\s+author", re.IGNORECASE),
            re.compile(r"DSC\d{4}:?", re.IGNORECASE), # Course codes like DSC3108
            re.compile(r"Lecture\s+\d+", re.IGNORECASE)
        ]
        
        # Look at the first 30 lines
        for i, line in enumerate(lines[:30]):
            line = line.strip()
            if not line: continue
            # If we see an Abstract or Introduction, the header definitely ended
            if re.match(r"^(?:Abstract|1\.?\s*Introduction|Introduction)", line, re.IGNORECASE):
                content_start_idx = i
                break
            # If line is highly likely metadata (email or affiliation), keep looking
            if any(p.search(line) for p in header_patterns):
                content_start_idx = i + 1
        
        # Strip the identified header if it's not the whole document
        if content_start_idx > 0 and content_start_idx < len(lines) - 5:
            text = "\n".join(lines[content_start_idx:])

        # 2. Remove arXiv-style citation lines
        text = _ARXIV_PATTERN.sub("", text)

        # 3. Remove QA prompt template leakage
        for pat in _QA_PROMPT_PATTERNS:
            text = pat.sub("", text)

        # 4. Split into paragraphs and filter
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        filtered = []
        for p in paragraphs:
            words = p.split()
            # Skip very short fragments (likely figure captions, labels)
            if len(words) < 12 and (_CAPTION_NOISE.match(p) or any(
                x in p.lower() for x in ("figure", "table", "fig.", "tab.")
            )):
                continue
            # Skip very short lines that look like reference entries (avoid body text)
            if len(words) < 12 and _REF_LINE.match(p):
                continue
            filtered.append(p)

        text = "\n\n".join(filtered)

        # 5. Remove stray URLs
        text = re.sub(r"https?://\S+", "", text)
        # Collapse excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Sanitize text by removing excessive whitespace, merging hyphens, and truncating references."""
        if not text:
            return ""
        
        # 1. Truncate at References/Bibliography (common in academic papers)
        # Avoid truncating if "References" is at the start or mid-sentence
        ref_markers = [
            r'\n\s*References\s*\n', 
            r'\n\s*BIBLIOGRAPHY\s*\n', 
            r'\n\s*Works Cited\s*\n'
        ]
        for marker in ref_markers:
            match = re.search(marker, text, re.IGNORECASE)
            if match:
                text = text[:match.start()]
                break

        # 2. Fix hyphenated line-breaks: "syn-\nthesized" -> "synthesized"
        # This is the #1 cause of "garbled" words in PDF parsing
        # Handles optional spaces after the newline which often occur in indented text
        text = re.sub(r'(\w+)-\n\s*(\w+)', r'\1\2', text)

        # 3. Strip URLs to reduce noise (models often hallucinate on long URLs)
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # 4. Remove excessive citation parentheticals e.g. (Author et al., 2023)
        # Often these clutter the context window for small models
        # text = re.sub(r'\(\w+ et al\., \d{4}\)', '', text) # Keeping it simple for now

        # 5. Split into lines to identify repeating headers/footers
        lines = text.splitlines()
        if len(lines) > 10:
            from collections import Counter
            # Normalize for comparison: lowercase, strip, remove slide/page numbers
            def normalize_line(l):
                l = l.strip().lower()
                l = re.sub(r'slide\s+\d+\s+of\s+\d+', '', l)
                l = re.sub(r'page\s+\d+(\s+of\s+\d+)?', '', l)
                l = re.sub(r'^\d+$', '', l) # Just a number
                return re.sub(r'\s+', ' ', l).strip()
            
            normalized_lines = [normalize_line(l) for l in lines]
            line_counts = Counter(normalized_lines)
            
            # Identify lines that appear frequently (more than 10% of pages OR at least 3 times in 20+ lines)
            # Threshold: if a normalized line repeats, it's likely a header/footer
            filtered_lines = []
            for i, line in enumerate(lines):
                norm = normalized_lines[i]
                if not norm: # Keep empty lines for structure, or skip if they were just numbers
                    if line.strip(): # It was just a number or slide ref
                        continue
                    filtered_lines.append(line)
                    continue
                    
                count = line_counts[norm]
                # High frequency threshold for slides: if it appears > 15% of the time, or >= 3 times in a decent doc
                if count >= 3 and count > (len(lines) // 50): 
                    # Potential header. But don't remove if it's very long (likely actual content that happens to repeat?)
                    # Actually, long repeating lines are even MORE likely to be headers (e.g. "Faculty of Engineering...")
                    continue
                filtered_lines.append(line)
            text = "\n".join(filtered_lines)
        else:
            text = "\n".join(lines)

        # 6. Remove control characters and non-printable characters
        text = "".join(char for char in text if char.isprintable() or char in "\n\r\t")
        
        # 7. Normalize whitespace
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
