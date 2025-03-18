import cv2
import numpy as np

def correct_perspective(image):
    """Eğik plakaları düzeltmek için perspektif dönüşümü uygular."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 200)

    # Konturları bul
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:  # Plaka genellikle dörtgen olduğu için
            pts1 = np.float32([point[0] for point in approx])  # Köşe noktaları
            break
    else:
        return image  # Plaka bulunamazsa orijinal resmi döndür

    # Hedef plaka boyutu (standart bir oran)
    width = 200
    height = 50
    pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])

    # Perspektif dönüşüm matrisi
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(image, matrix, (width, height))

    return warped
