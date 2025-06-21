from ultralytics import YOLO
import cv2

model = YOLO("../brands.pt")  # Doğru model yolunu kullan

class_names = model.names

def detect_brand(image_path):
    try:
        results = model(image_path)[0]
        image = cv2.imread(image_path)

        if len(results.boxes) == 0:
            print("⚠️ Marka bulunamadı.")
            return "unknown"

        # Birden fazla kutu varsa en yüksek confidence'lıyı seç
        highest_conf = 0
        best_label = "unknown"

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = class_names[cls_id] if cls_id < len(class_names) else f"id:{cls_id}"

            if conf > highest_conf:
                highest_conf = conf
                best_label = label

        print(f"✅ En iyi tahmin: {best_label} ({highest_conf:.2f})")
        return best_label

    except Exception as e:
        print(f"🔥 Marka tespiti hatası: {e}")
        return "unknown"
