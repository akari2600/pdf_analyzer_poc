import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import time

@dataclass
class LayoutElement:
    type: str
    bbox: Tuple[int, int, int, int]  # x, y, width, height

def preprocess_image(image):
    """Convert image to grayscale OpenCV image and apply thresholding."""
    print("Preprocessing image...")
    start_time = time.time()
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    print(f"Preprocessing completed in {time.time() - start_time:.2f} seconds")
    return binary

def detect_layout_elements(binary_image, granularity=50):
    """Detect layout elements using contour detection with adjustable granularity."""
    print("Detecting layout elements...")
    start_time = time.time()
    
    # Apply morphological operations to merge nearby elements
    kernel_size = max(1, int(min(binary_image.shape) * granularity / 1000))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    dilated = cv2.dilate(binary_image, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    elements = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        element_type = classify_element(binary_image[y:y+h, x:x+w], w, h)
        elements.append(LayoutElement(element_type, (x, y, w, h)))
    print(f"Detected {len(elements)} elements in {time.time() - start_time:.2f} seconds")
    return elements

def classify_element(roi, width, height):
    """Classify the type of layout element based on its characteristics."""
    aspect_ratio = width / height
    area = width * height
    pixel_density = np.sum(roi) / (width * height * 255)

    if aspect_ratio > 5 or aspect_ratio < 0.2:
        return "line"
    elif pixel_density > 0.5:
        return "image"
    elif area > 1000 and pixel_density > 0.1:
        return "text_block"
    elif width > 100 and height > 100:
        return "table"
    else:
        return "unknown"

def analyze_spatial_relationships(elements):
    """Analyze spatial relationships between layout elements."""
    print("Analyzing spatial relationships...")
    start_time = time.time()
    relationships = []
    for i, elem1 in enumerate(elements):
        for j, elem2 in enumerate(elements[i+1:], start=i+1):
            relationship = get_relationship(elem1, elem2)
            if relationship:
                relationships.append((i, j, relationship))
    print(f"Analyzed {len(relationships)} relationships in {time.time() - start_time:.2f} seconds")
    return relationships

def get_relationship(elem1, elem2):
    """Determine the spatial relationship between two elements."""
    x1, y1, w1, h1 = elem1.bbox
    x2, y2, w2, h2 = elem2.bbox
    
    if abs(y1 - y2) < 10:
        return "horizontally_aligned"
    elif abs(x1 - x2) < 10:
        return "vertically_aligned"
    elif x1 < x2 < x1 + w1 and y1 < y2 < y1 + h1:
        return "contains"
    elif x2 < x1 < x2 + w2 and y2 < y1 < y2 + h2:
        return "contained_by"
    else:
        return None

def analyze_layout(image, granularity=50):
    """Analyze the layout of the given image with adjustable granularity."""
    print("Starting layout analysis...")
    start_time = time.time()
    binary_image = preprocess_image(image)
    elements = detect_layout_elements(binary_image, granularity)
    relationships = analyze_spatial_relationships(elements)
    print(f"Layout analysis completed in {time.time() - start_time:.2f} seconds")
    return {
        'elements': elements,
        'relationships': relationships
    }