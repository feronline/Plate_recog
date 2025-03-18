import cv2
import numpy as np

def deskew_plate(plate_image):
    gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return plate_image  # Eğer kontur bulunamazsa, orijinal görüntüyü döndür

    largest_contour = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(largest_contour)
    (center, (width, height), angle) = rect

    # Eğer dikdörtgen yanlış yönlendirilmişse düzelt
    if width < height:
        angle = angle - 90

    angle = -angle  # OpenCV'nin döndürme yönüne uygun hale getir

    # 📌 Eğimi kontrol et:
    if abs(angle) < 4:
        return plate_image  # Eğer açı 5°'den küçükse hiç döndürme

    # 📌 Eğer açı 5°'den büyükse, maksimum 5° döndür
    if angle > 5:
        angle = 5
    else:
        angle = -5

    (h, w) = plate_image.shape[:2]
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(plate_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated
