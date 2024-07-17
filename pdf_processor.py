import fitz  # PyMuPDF
import numpy as np

def load_pdf(pdf_path, page_number=0, zoom=1):
    """
    Load a specific page from a PDF file and return it as a numpy array.
    
    :param pdf_path: Path to the PDF file
    :param page_number: Page number to load (0-indexed)
    :param zoom: number by which to multiply the matrix
    :return: Tuple of (image as numpy array, total number of pages)
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    if page_number < 0 or page_number >= total_pages:
        raise ValueError(f"Invalid page number. The document has {total_pages} pages.")
    
    page = doc.load_page(page_number)
    mat = fitz.Matrix(zoom, zoom)  # use zoom value 
    pix = page.get_pixmap(matrix=mat)
    
    # Convert pixmap to numpy array
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    
    # If the image is RGBA, convert it to RGB
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    doc.close()
    return img_array, total_pages

def get_total_pages(pdf_path):
    """
    Get the total number of pages in a PDF file.
    
    :param pdf_path: Path to the PDF file
    :return: Total number of pages
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    return total_pages