# PDF Analyzer PoC

This project is a Proof of Concept (PoC) for a PDF Analyzer tool. It provides a graphical user interface for loading PDF files, analyzing their layout, and visualizing the results.

## Features

- Load PDF files and convert them to images
- Analyze the layout of PDF pages
- Visualize layout analysis results with adjustable thresholds
- Option to preprocess images before analysis
- Display of detected horizontal and vertical cuts in the document layout

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pdf_analyzer_poc.git
   cd pdf_analyzer_poc
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command from the project root directory:

```
python gui.py
```

This will launch the graphical user interface. From there, you can:

1. Click "Choose File" to select a PDF file for analysis.
2. Adjust the X and Y thresholds as needed.
3. Toggle the "Enable Preprocessing" checkbox if desired.
4. Click "Analyze Layout" to process the PDF and view the results.

## Project Structure

- `gui.py`: Main entry point of the application, contains the GUI implementation
- `pdf_processor.py`: Handles loading and processing of PDF files
- `image_analyzer.py`: Contains functions for image preprocessing and layout analysis
- `main.py`: Currently not used, may be used for future command-line interface
- `requirements.txt`: Lists all Python dependencies for the project
- `test_pdfs/`: Directory containing PDF files for testing (ignored in git except for sample.pdf)

## Contributing

This is a Proof of Concept project. For any major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)