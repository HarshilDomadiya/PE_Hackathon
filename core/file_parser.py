"""
File Parser Engine for PDF (Text Layer + Robust OCR Fallback), DOCX, TXT, MD, JSON, CSV
Team 24 | Venue: MB314 | Problem 22

Robust PDF Extraction Architecture:
1. Primary: Text extraction using pypdf & PyMuPDF (fitz) text layer
2. Fallback OCR: Page-by-page high-resolution image rendering + EasyOCR (local, zero cloud APIs)
3. Multi-page order preservation & fact preservation
"""

import sys
import os
import re

def extract_pdf_with_ocr_fallback(file_path: str) -> str:
    """
    Extracts text from PDF files:
    - Step 1: Attempts normal text extraction using pypdf & PyMuPDF (fitz).
    - Step 2: If text is missing or < 30 chars (scanned/image PDF), automatically falls back to OCR.
    - Step 3: Processes pages in exact page order and normalizes whitespace without changing facts.
    """
    extracted_pages = []
    
    # --- Step 1: Primary Text Extraction (pypdf & PyMuPDF) ---
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        for idx, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt and len(txt.strip()) > 5:
                extracted_pages.append(txt.strip())
    except Exception:
        pass

    # If pypdf missed some text, try PyMuPDF text layer
    if not extracted_pages:
        try:
            import pymupdf
            doc = pymupdf.open(file_path)
            for page in doc:
                txt = page.get_text()
                if txt and len(txt.strip()) > 5:
                    extracted_pages.append(txt.strip())
        except Exception:
            pass

    combined_text = "\n\n".join(extracted_pages).strip()

    # Check if extracted text is meaningful (> 30 characters)
    if len(combined_text) > 30:
        # Clean up light formatting artifacts
        cleaned = re.sub(r'[ \t]+', ' ', combined_text)
        return cleaned

    # --- Step 2: Automatic Fallback to Local OCR (Scanned / Image PDF) ---
    ocr_pages = []
    try:
        import pymupdf
        import easyocr

        doc = pymupdf.open(file_path)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)

        for page_idx, page in enumerate(doc, start=1):
            # Render high-resolution page pixmap
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")

            # Run EasyOCR page-by-page preserving order
            results = reader.readtext(img_bytes, detail=0)
            page_text = " ".join(results).strip()

            if page_text:
                ocr_pages.append(page_text)

    except Exception as ocr_err:
        pass

    if ocr_pages:
        full_ocr_text = "\n\n".join(ocr_pages).strip()
        # Normalize whitespace while preserving numbers, dates, names verbatim
        normalized_ocr = re.sub(r'[ \t]+', ' ', full_ocr_text)
        
        return f"[PDF processed successfully using OCR.]\n\n{normalized_ocr}"

    # --- Step 3: Error Message if Both Methods Fail ---
    return "Unable to extract readable text from this PDF using text extraction or OCR. Please verify that the PDF contains readable pages."


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_pdf_with_ocr_fallback(file_path)

    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            return f"Error extracting text from DOCX: {str(e)}"

    else:
        # Plain text / Markdown / JSON / CSV / HTML
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file: {str(e)}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
        text = extract_text_from_file(target_path)
        print("PARSED_TEXT_START")
        print(text)
