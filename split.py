import os
import random

# Ana klasör
dataset_path = "C:/Users/ferha/Desktop/Plate_recog/data/images"

# Tüm .jpg dosyalarını al
image_files = [f for f in os.listdir(dataset_path) if f.endswith(".jpg")]

# Rastgele karıştır ve %80 eğitim, %20 doğrulama olarak böl
random.shuffle(image_files)
train_split = int(len(image_files) * 0.8)

train_files = image_files[:train_split]
val_files = image_files[train_split:]

# train.txt ve val.txt dosyalarını oluştur
with open(os.path.join(dataset_path, "train.txt"), "w") as f:
    for img in train_files:
        f.write(os.path.join(dataset_path, img) + "\n")

with open(os.path.join(dataset_path, "val.txt"), "w") as f:
    for img in val_files:
        f.write(os.path.join(dataset_path, img) + "\n")

# YOLOv11s için data.yaml dosyası
yaml_content = f"""
train: {os.path.join(dataset_path, "train.txt")}
val: {os.path.join(dataset_path, "val.txt")}

nc: 1
names: ['plate']
"""

# data.yaml dosyasını kaydet
with open(os.path.join(dataset_path, "data.yaml"), "w") as f:
    f.write(yaml_content)

print("✅ YOLOv11s için veri yapısı oluşturuldu!")
