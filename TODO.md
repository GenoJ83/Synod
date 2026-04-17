# OCR Implementation Plan - Progress Tracker

## Information Gathered:
- Current extraction: PyMuPDF (PDF text only), python-pptx (text shapes only) - no image OCR.
- Files to edit: backend/app/ingestion/extractor_service.py (add OCR logic), requirements.txt (+ pytesseract pdf2image), Dockerfile (+ tesseract poppler).

## Pending Steps:
- [x] Step 1: Update requirements.txt + Dockerfile for OCR deps
- [x] Step 2: Implement OCR in extractor_service.py (PDF images → Tesseract)
- [ ] Step 3: Test extraction on image-heavy PDF
- [ ] Step 4: Commit/push

## Completed:
- Step 1: Added pytesseract pdf2image Pillow, system deps (tesseract poppler)
- Step 2: OCR logic in _extract_from_pdf (PyMuPDF pixmap → Tesseract), graceful fallback
