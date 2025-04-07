import cv2
import numpy as np

def remove_blue_area(img):
    """Görüntüdeki mavi alanları tespit eder ve beyaza boyar."""

    # BGR'den HSV renk uzayına geçiş
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Mavi renk için HSV aralığı
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])

    # Mavi alanları maskele
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Mavi alanları beyaza çevir
    img[mask > 0] = [255, 255, 255]

    return img
def enhance_plate(img):
    """Plaka görüntüsünü OCR için iyileştirir. Mavi alanı renk koruma ile iyileştirir."""

    # Görüntü boyutlarını al
    height, width, _ = img.shape

    # Sol taraftaki %10'luk alanı seç (ROI)
    roi_end = int(width * 0.1)  # Sol %10 genişliğin son noktası
    roi = img[:, :roi_end]  # Sol %10'luk alan (ROI)

    # ROI'ye kontrast optimizasyonu (parlaklık artırma)
    enhanced_roi = cv2.convertScaleAbs(roi, alpha=1.2, beta=30)  # Kontrast ve parlaklık artırma

    # Güncellenmiş ROI'yi orijinal görüntüye geri yerleştir
    img[:, :roi_end] = enhanced_roi

    # Görüntünün geri kalan %90'lık alanını gri tonlamaya çevir
    gray = cv2.cvtColor(remove_blue_area(img), cv2.COLOR_BGR2GRAY)

    # Gürültü azaltma
    gray = cv2.bilateralFilter(gray, 11, 90, 90)

    # Adaptif Threshold uygulama
    thresholded = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Kenar keskinleştirme
    kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(thresholded, -1, kernel_sharpen)

    # Morfolojik işlemler
    kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    eroded = cv2.erode(sharpened, kernel_morph, iterations=1)
    dilated = cv2.dilate(eroded, kernel_morph, iterations=1)

    return dilated
