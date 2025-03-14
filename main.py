import cv2
import numpy as np
import os

dataset_path = "C:/Users/ferha/Desktop/Plate_recog/data/images"
bbox_path = "C:/Users/ferha/Desktop/Plate_recog/data/labelled_images"
max_images = 1955

for i in range(1, max_images + 1):
    image_path = os.path.join(dataset_path, f"{i}.jpg")
    label_path = os.path.join(dataset_path, f"{i}.txt")
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    with open(label_path, 'r') as file:
        data = file.readline().strip().split()

    _, x_center, y_center, w, h = map(float, data)

    x_center, y_center, w ,h = int(x_center * width), int(y_center * height), int(w * width), int(h * height)

    x1, y1 = max(0, int(x_center - w / 2)), max(0, int(y_center - h / 2))
    x2, y2 = min(width, int(x_center + w / 2)), min(height, int(y_center + h / 2))


    mask = np.zeros((height, width), dtype=np.uint8)
    mask[y1:y2, x1:x2] = 255

    output_image_path = os.path.join(bbox_path, f"{i}.jpg")
    cv2.imwrite(output_image_path, mask)

print("Done")
