import cv2
import numpy as np

def enhance_plate(plate_image):
    # Sol kısmı (TR bandı) kırp
    h, w = plate_image.shape[:2]
    crop_x = int(w * 0.10)
    plate_image = plate_image[:, crop_x:]

    # Gerekliyse küçült
    if max(h, w) > 200:
        plate_image = cv2.resize(plate_image, (300, 80))  # örnek sabit boyut

    # Griye çevir
    gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)

    # Basit threshold
    _, binary = cv2.threshold(gray, 64, 255, cv2.THRESH_BINARY)

    # Hafif blur
    blurred = cv2.GaussianBlur(binary, (3, 3), 0)

    # Morfolojik kapatma (küçük boşlukları düzeltmek için)
    kernel = np.ones((2, 2), np.uint8)
    deskewed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel, iterations=1)

    return deskewed