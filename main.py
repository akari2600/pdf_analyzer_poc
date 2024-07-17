from pdf_processor import load_pdf, get_pdf_info
from image_analyzer import preprocess_image, analyze_layout

def main(pdf_path):
    # Load PDF
    pdf_info = get_pdf_info(pdf_path)
    print(f"PDF Info: {pdf_info}")

    # Convert first page to image
    image = load_pdf(pdf_path)

    # Preprocess image
    cv_image = preprocess_image(image)

    # Analyze layout
    layout = analyze_layout(cv_image, x_threshold=200, y_threshold=200)
    print(f"Layout analysis: {layout}")

    # Here you would add more processing steps as needed

if __name__ == "__main__":
    pdf_path = "test_pdfs/sample.pdf"  # Replace with your test PDF
    main(pdf_path)
