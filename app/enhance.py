import cv2
import numpy as np
from skew import deskew_plate


def enhance_plate(plate_image):

    h, w = plate_image.shape[:2]

    crop_x = int(w * 0.085)
    plate_image = plate_image[:, crop_x:]

    resized = cv2.resize(plate_image, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized.copy()

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    _, binary = cv2.threshold(blurred, 64, 255, cv2.THRESH_BINARY)

    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    kernel_close = np.ones((2, 2), np.uint8)
    result = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close, iterations=1)

    deskewed = deskew_plate(result)

    return deskewed