from pdf2image import convert_from_path
import numpy as np
import PyPDF2

def load_pdf(file_path):
    """Load a PDF file and return its first page as an image."""
    print(f"Converting PDF to image: {file_path}")
    images = convert_from_path(file_path, dpi=200, first_page=1, last_page=1)
    if images:
        return np.array(images[0])
    else:
        raise ValueError("Failed to convert PDF to image")

def get_pdf_info(file_path):
    """Get basic information about the PDF."""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        info = {
            'num_pages': len(reader.pages),
            'metadata': reader.metadata
        }
    return info
