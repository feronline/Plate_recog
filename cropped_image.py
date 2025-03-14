import cv2
import os

bbox_path = "C:/Users/ferha/Desktop/Plate_recog/data/labelled_images"
cropped_path = "C:/Users/ferha/Desktop/Plate_recog/data/cropped_images"

image_files = [f for f in os.listdir(bbox_path) if f.endswith(".jpg")]

for image_file in image_files:
    file_name = os.path.splitext(image_file)[0]

    image_path = os.path.join(bbox_path, image_file)

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 5, 50, apertureSize=5)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    plate_region = None
    max_area = 0
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        area = w * h
        if area > max_area:
            max_area = area
            plate_region = (x,y,w,h)

    if plate_region:
        x, y, w, h = plate_region
        plate_crop = image[y:y+h, x:x+w]

        if plate_crop.size > 0:
            crpped_image_path = os.path.join(cropped_path, f"{file_name}.jpg")
            cv2.imwrite(crpped_image_path, plate_crop)

print("done")

