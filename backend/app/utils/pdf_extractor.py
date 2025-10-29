# app/utils/pdf_extractor.py

import io
from PyPDF2 import PdfReader


def extract_text_from_pdf(file: bytes) -> str:
    """
    Extracts text from a PDF file.
    
    Args:
        file (bytes): The binary content of the uploaded PDF file.
    
    Returns:
        str: Extracted text content from the PDF.
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(file))
        text = ""

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # Clean the extracted text
        cleaned_text = text.strip().replace('\n', ' ').replace('\r', '')
        return cleaned_text

    except Exception as e:
        print(f"⚠️ Error extracting PDF text: {e}")
        return ""
