import cv2
import numpy as np


def deskew_plate(plate_image):
    """
    Eğimli olarak kırpılmış plaka görüntüsünü düzeltir.

    Args:
        plate_image: Kırpılmış plaka görüntüsü

    Returns:
        Düzeltilmiş plaka görüntüsü
    """
    # Görüntünün boyutlarını al
    h, w = plate_image.shape[:2]

    # Gri tonlamaya dönüştür
    if len(plate_image.shape) == 3:  # Renkli görüntü ise
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
    else:  # Zaten gri tonlamalı ise
        gray = plate_image.copy()

    # Gürültüyü azalt
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Görüntüyü ikili (binary) hale getir
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morfolojik işlemler (küçük gürültüleri temizle)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Konturları bul
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return plate_image  # Kontur bulunamadı, orijinal görüntüyü döndür

    # Tüm konturları birleştir (plaka karakterlerinin hepsini kapsayan bir kontur elde etmek için)
    all_contours = np.vstack([contour for contour in contours])

    # Minimum döndürülmüş dikdörtgeni bul
    rect = cv2.minAreaRect(all_contours)
    angle = rect[2]

    # Açıyı düzelt (OpenCV bazen -90 ile 0 arasında, bazen 0 ile 90 arasında değer döndürür)
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    # Döndürme matrisini oluştur
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Görüntüyü döndür
    rotated = cv2.warpAffine(plate_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated

