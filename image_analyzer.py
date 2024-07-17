import cv2
import numpy as np

def preprocess_image(image):
    """Convert image to grayscale OpenCV image."""
    if len(image.shape) == 3:
        cv_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        cv_image = image
    return cv_image

def x_cut(image, threshold):
    row_sums = np.sum(image, axis=1)
    max_sum = image.shape[1] * 255  # maximum possible sum for a row
    threshold_value = max_sum * (1 - threshold / 100)  # convert percentage to absolute value
    cuts = np.where(row_sums < threshold_value)[0]
    return get_ranges(cuts)

def y_cut(image, threshold):
    col_sums = np.sum(image, axis=0)
    max_sum = image.shape[0] * 255  # maximum possible sum for a column
    threshold_value = max_sum * (1 - threshold / 100)  # convert percentage to absolute value
    cuts = np.where(col_sums < threshold_value)[0]
    return get_ranges(cuts)

def get_ranges(cuts):
    ranges = []
    start = None
    for i, cut in enumerate(cuts):
        if start is None:
            start = cut
        elif i == len(cuts) - 1 or cuts[i+1] - cut > 1:
            ranges.append((start, cut))
            start = None
    return ranges

def analyze_layout(image, x_threshold, y_threshold):
    image = preprocess_image(image)
    x_cuts = x_cut(image, x_threshold)
    y_cuts = y_cut(image, y_threshold)
    return {'x_cuts': x_cuts, 'y_cuts': y_cuts}
