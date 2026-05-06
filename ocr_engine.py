"""
ocr_engine.py — TenderShield AI
Extracts text from PDF and image files.
Falls back gracefully if cv2 is not installed.
"""

import os
import pytesseract
from PIL import Image

# Windows Tesseract path — change if needed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# Optional: try importing cv2, fall back to PIL if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[ocr_engine] cv2 not found — using PIL for image processing (install opencv-python for better results)")


def extract_text_from_pdf(file_path: str) -> str:
    """
    Master function:
    - For PDFs: extracts text directly, falls back to OCR per page
    - For images: runs OCR with preprocessing
    """
    if not os.path.exists(file_path):
        return ""

    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        return _extract_from_pdf(file_path)
    elif ext in ("jpg", "jpeg", "png", "tiff", "bmp"):
        return _extract_from_image(file_path)
    else:
        return ""


def _extract_from_pdf(file_path: str) -> str:
    """Try direct text extraction first; OCR page-by-page if scanned."""
    try:
        import fitz   # PyMuPDF
    except ImportError:
        return "Install PyMuPDF: pip install pymupdf"

    full_text = ""
    doc = fitz.open(file_path)

    # CRITICAL FIX: Large PDFs (800+ pages) cause timeouts.
    # Eligibility criteria are almost always in the first 10-30 pages (Notice Inviting Tender).
    max_pages = min(30, len(doc))
    for i in range(max_pages):
        page = doc[i]
        text = page.get_text("text").strip()

        if len(text) < 50:
            # Scanned page — render and OCR
            mat = fitz.Matrix(2.0, 2.0)   # 2x zoom for better accuracy
            pix = page.get_pixmap(matrix=mat)
            import io
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = _ocr_image(img)

        full_text += f"\n--- PAGE {i+1} ---\n{text}"

    doc.close()
    print("\n[OCR] Extracted text preview:\n", full_text[:500])
    return _clean(full_text)


def _extract_from_image(file_path: str) -> str:
    """OCR an image file with preprocessing."""
    if CV2_AVAILABLE:
        import cv2, numpy as np
        img = cv2.imread(file_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Threshold for clarity
        _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        pil_img = Image.fromarray(gray)
    else:
        pil_img = Image.open(file_path).convert("L")  # grayscale with PIL

    text = _ocr_image(pil_img)
    print("\n[OCR] Image text preview:\n", text[:500])
    return _clean(text)


def _ocr_image(pil_img: Image.Image) -> str:
    """Run Tesseract OCR on a PIL image."""
    try:
        return pytesseract.image_to_string(pil_img, config="--psm 6 -l eng")
    except Exception as e:
        return f"[OCR Error: {e}]"


def get_document_metadata(file_path: str) -> dict:
    """
    Extract PDF metadata for fraud detection.
    Returns creation date, modification date, author, software used.
    """
    try:
        import fitz
        doc  = fitz.open(file_path)
        meta = doc.metadata
        page_count = len(doc)
        doc.close()
        return {
            "author":     meta.get("author",       ""),
            "creator":    meta.get("creator",      ""),
            "producer":   meta.get("producer",     ""),
            "created":    meta.get("creationDate", ""),
            "modified":   meta.get("modDate",      ""),
            "title":      meta.get("title",        ""),
            "page_count": page_count
        }
    except Exception as e:
        return {"error": str(e)}


def _clean(text: str) -> str:
    """Remove excessive whitespace and non-printable chars."""
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}',  ' ',    text)
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()
