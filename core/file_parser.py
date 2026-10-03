"""
File Parser Engine for PDF, DOCX, TXT, MD, JSON, CSV
Team 24 | Venue: MB314 | Problem 22
"""

import sys
import os
import json

def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            extracted = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted.append(txt)
            return "\n\n".join(extracted)
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"

    elif ext in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
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
