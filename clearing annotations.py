import json
from collections import defaultdict

# JSON dosyasını yükleme
json_path = "C:/Users/ferha/Desktop/Plate_recog/data/annotations.json"
with open(json_path, "r") as file:
    data = json.load(file)

# Annotation sayısını takip etmek için sözlük
image_annotation_count = defaultdict(int)
zero_area_annotations = []

total_annotations = len(data["annotations"])
print(f"Toplam annotation sayısı: {total_annotations}")

# Her annotation'ı kontrol et
for annotation in data["annotations"]:
    image_annotation_count[annotation["image_id"]] += 1
    if annotation["area"] == 0:
        zero_area_annotations.append(annotation["id"])

# Tek annotation içeren görüntüler
single_annotation_images = sum(1 for count in image_annotation_count.values() if count == 1)
multiple_annotation_images = sum(1 for count in image_annotation_count.values() if count > 1)

print(f"Tek annotation içeren görüntüler: {single_annotation_images}")
print(f"Birden fazla annotation içeren görüntüler: {multiple_annotation_images}")
print(f"Sıfır alanlı annotation sayısı: {len(zero_area_annotations)}")

if zero_area_annotations:
    print("Sıfır alanlı annotation ID'leri:", zero_area_annotations[:10])