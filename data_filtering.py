import cv2
import os
import numpy as np

cropped_path = "C:/Users/ferha/Desktop/Plate_recog/data/cropped_images"

image_files = [f for f in os.listdir(cropped_path) if f.endswith(".jpg")]

for image_file in image_files:
    image_path = os.path.join(cropped_path, image_file)
    image = cv2.imread(image_path)

    h, w, _ = image.shape
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)

    if mean_brightness < 50 or mean_brightness > 200:
        print(f"Deleting: {image_file} (Brightness: {mean_brightness:.2f})")
        os.remove(image_path)
        continue

    if h < 30 or w < 100:
        print(f"Deleting: {image_file} (Size: {w}x{h})")
        os.remove(image_path)
        continue

    aspect_ratio = w / float(h)
    if aspect_ratio < 3.0 or aspect_ratio > 5.5:
        print(f"Deleting: {image_file} (Ratio: {aspect_ratio:.2f})")
        os.remove(image_path)
        continue

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()

    if variance < 100:
        print(f"Deleting: {image_file} (Blur: {variance:.2f})")
        os.remove(image_path)

print("done")
