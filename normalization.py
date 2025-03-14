import json

json_path = "C:/Users/ferha/Desktop/Plate_recog/data/annotations.json"

with open(json_path, "r") as f:
    data = json.load(f)

annotations = data["annotations"]

areas = [ann["area"] for ann in annotations]

print(f"Toplam plaka sayısı: {len(areas)}")
print(f"En küçük plaka alanı: {min(areas)}")
print(f"En büyük plaka alanı: {max(areas)}")
print(f"Ortalama plaka alanı: {sum(areas)/len(areas)}")
