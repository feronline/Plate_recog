import os
import json
import cv2

# Yol tanımları
image_path = "C:/Users/ferha/Desktop/Plate_recog/data/images"
mask_path = "C:/Users/ferha/Desktop/Plate_recog/data/labelled_images"
output_json = "C:/Users/ferha/Desktop/Plate_recog/data/annotations.json"

# COCO formatı için temel yapı
coco_format = {
    "images": [],
    "annotations": [],
    "categories": [{"id": 1, "name": "plate"}]
}

image_files = sorted([f for f in os.listdir(image_path) if f.endswith(".jpg")])
annotation_id = 1  # Annotation ID'yi takip etmek için sayaç

for img_id, img_file in enumerate(image_files, start=1):
    img_name = os.path.splitext(img_file)[0]
    img_full_path = os.path.join(image_path, img_file)

    # Görüntü bilgilerini al
    image = cv2.imread(img_full_path)
    height, width, _ = image.shape

    coco_format["images"].append({
        "id": img_id,
        "file_name": img_file,
        "width": width,
        "height": height
    })

    # Maskeyi oku
    mask_file = os.path.join(mask_path, f"{img_name}.jpg")
    if os.path.exists(mask_file):
        mask = cv2.imread(mask_file, cv2.IMREAD_GRAYSCALE)

        # Tüm konturları bul
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # **En büyük konturu seç**
            largest_contour = max(contours, key=cv2.contourArea)

            # Alanı hesapla
            area = cv2.contourArea(largest_contour)

            # Eğer alan sıfırsa geç
            if area == 0:
                continue

            # Bounding box hesapla (x, y, w, h)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # COCO formatına uygun annotation ekle
            coco_format["annotations"].append({
                "id": annotation_id,
                "image_id": img_id,
                "category_id": 1,
                "segmentation": [largest_contour.flatten().tolist()],
                "area": area,
                "bbox": [x, y, w, h],
                "iscrowd": 0
            })

            annotation_id += 1  # Annotation ID'yi artır

# JSON dosyasına kaydet
with open(output_json, "w") as json_file:
    json.dump(coco_format, json_file, indent=4)

print("✅ Yeni JSON kaydedildi: annotations.json")
