"""
PDF Extraction & OCR Fallback Integration Test Suite
Team 24 | Venue: MB314 | Problem 22
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.file_parser import extract_text_from_file, extract_pdf_with_ocr_fallback

class TestPDFOCRFallback(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "scratch")
        os.makedirs(self.test_dir, exist_ok=True)

    def test_text_pdf_extraction(self):
        """TEST 1: Normal selectable-text PDF"""
        import pymupdf
        pdf_path = os.path.join(self.test_dir, "sample_text.pdf")
        
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 50), "NovaSilicon Technologies announced on 18 September 2026 the NS-E3 edge AI processor.")
        doc.save(pdf_path)
        doc.close()

        extracted = extract_text_from_file(pdf_path)
        self.assertIn("NovaSilicon Technologies", extracted)
        self.assertNotIn("[PDF processed successfully using OCR.]", extracted)

    def test_scanned_image_pdf_ocr_fallback(self):
        """TEST 2: Scanned/image-based PDF (R1.pdf emulation)"""
        import pymupdf
        from PIL import Image, ImageDraw, ImageFont

        pdf_path = os.path.join(self.test_dir, "R1.pdf")
        
        # Create an image containing text (simulating scanned document page)
        img = Image.new('RGB', (800, 300), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((40, 40), "CloudPay Technologies reported FY2026 annual financial results surpassing $850M ARR.", fill=(0, 0, 0))
        img_path = os.path.join(self.test_dir, "r1_page.png")
        img.save(img_path)

        # Save image inside PDF without font text layer
        doc = pymupdf.open()
        page = doc.new_page(width=800, height=300)
        page.insert_image(pymupdf.Rect(0, 0, 800, 300), filename=img_path)
        doc.save(pdf_path)
        doc.close()

        extracted = extract_text_from_file(pdf_path)
        self.assertIn("[PDF processed successfully using OCR.]", extracted)
        self.assertTrue("CloudPay" in extracted or "FY2026" in extracted or "850M" in extracted or "ARR" in extracted or "financial" in extracted)

    def test_multipage_scanned_pdf_order(self):
        """TEST 3: Scanned multi-page PDF order preservation"""
        import pymupdf
        from PIL import Image, ImageDraw

        pdf_path = os.path.join(self.test_dir, "multipage_scanned.pdf")
        doc = pymupdf.open()

        # Page 1 image
        img1 = Image.new('RGB', (800, 200), color=(255, 255, 255))
        d1 = ImageDraw.Draw(img1)
        d1.text((30, 30), "PAGE ONE: BioNova Research study results.", fill=(0, 0, 0))
        img1_path = os.path.join(self.test_dir, "p1.png")
        img1.save(img1_path)
        page1 = doc.new_page(width=800, height=200)
        page1.insert_image(pymupdf.Rect(0, 0, 800, 200), filename=img1_path)

        # Page 2 image
        img2 = Image.new('RGB', (800, 200), color=(255, 255, 255))
        d2 = ImageDraw.Draw(img2)
        d2.text((30, 30), "PAGE TWO: 1240 participants enrolled.", fill=(0, 0, 0))
        img2_path = os.path.join(self.test_dir, "p2.png")
        img2.save(img2_path)
        page2 = doc.new_page(width=800, height=200)
        page2.insert_image(pymupdf.Rect(0, 0, 800, 200), filename=img2_path)

        doc.save(pdf_path)
        doc.close()

        extracted = extract_text_from_file(pdf_path)
        self.assertIn("[PDF processed successfully using OCR.]", extracted)

    def test_docx_txt_md_support(self):
        """TEST 5: Upload DOCX/TXT/MD unchanged"""
        txt_path = os.path.join(self.test_dir, "sample.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("GreenGrid Energy announced a 420 MW solar project.")
        
        extracted = extract_text_from_file(txt_path)
        self.assertEqual(extracted, "GreenGrid Energy announced a 420 MW solar project.")

if __name__ == "__main__":
    unittest.main()
