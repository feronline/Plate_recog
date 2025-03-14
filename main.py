import cv2
import numpy as np
import os

dataset_path = "C:/Users/ferha/Desktop/Plate_recog/data/images"
output_path = "C:/Users/ferha/Desktop/Plate_recog/data/labelled_images"
max_images = 100

for i in range(1, max_images + 1):
    image_path = os.path.join(dataset_path, f"{i}.jpg")
    label_path = os.path.join(dataset_path, f"{i}.txt")
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    with open(label_path, 'r') as file:
        data = file.readline().strip().split()

    _, x_center, y_center, w, h = map(float, data)

    x_center, y_center, w ,h = int(x_center * width), int(y_center * height), int(w * width), int(h * height)

    x1, y1 = int(x_center - w / 2), int(y_center - h / 2)
    x2, y2 = int(x_center + w / 2), int(y_center + h / 2)


    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)

    output_image_path = os.path.join(output_path, f"{i}.jpg")
    cv2.imwrite(output_image_path, image)

print("Done")
