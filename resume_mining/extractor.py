from typing import Optional

import io
from pathlib import Path

from PIL import Image
import fitz  # PyMuPDF


def extract_text_from_pdf(path: str, enable_ocr: bool = False) -> str:
    """Extract text from a PDF. If text layer is empty and enable_ocr, run OCR.

    Args:
            path: PDF file path.
            enable_ocr: Whether to use OCR fallback for scanned PDFs.

    Returns:
            Extracted text as UTF-8 string.
    """
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(str(pdf_path))

    # Try text layer first (no OCR)
    text = ""
    try:
        text_chunks = []
        with fitz.open(str(pdf_path)) as doc:
            for page in doc:
                text_chunks.append(page.get_text("text") or "")
        text = "\n".join(text_chunks).strip()
    except Exception:
        text = ""

    if text or not enable_ocr:
        return text

    # OCR fallback using PyMuPDF for rendering (no Poppler) + pytesseract
    try:
        import pytesseract
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "OCR dependency 'pytesseract' not installed. Install pytesseract."
        ) from exc

    ocr_text_chunks = []
    with fitz.open(str(pdf_path)) as doc:
        # 200 DPI is a reasonable trade-off for OCR accuracy vs speed
        zoom = 200.0 / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text_chunks.append(
                pytesseract.image_to_string(img, lang="fas+eng")
            )
    return "\n".join(ocr_text_chunks)
