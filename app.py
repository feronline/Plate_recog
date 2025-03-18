import cv2
import os
import tkinter as tk
from tkinter import filedialog, Button, Label, Canvas
from PIL import Image, ImageTk
from detection import detect_plates
from enhance import enhance_plate
from skew import deskew_plate
from ocr import ocr_plate

# Uygulama penceresi
root = tk.Tk()
root.title("Plate Detection App")
root.geometry("800x600")

# OCR sonucunu göstermek için bir Label ekleyelim
ocr_result_label = Label(root, text="OCR Result: ", font=("Arial", 16))
ocr_result_label.pack(pady=10)

# Klasör oluştur ve sırayla isimlendirme için fonksiyon
def get_next_plate_path():
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    file_count = len([name for name in os.listdir(output_dir) if name.startswith("plate_") and name.endswith(".jpg")])
    return os.path.join(output_dir, f"plate_{file_count + 1}.jpg")

def select_image():
    image_path = filedialog.askopenfilename(title='Choose an image', filetypes=[('Image Files', '*.jpg *.jpeg *.png')])
    if image_path:
        model_path = "best.onnx"
        result_img, bounding_boxes = detect_plates(model_path, image_path)

        if result_img is not None and len(bounding_boxes) > 0:
            image = cv2.imread(image_path)

            for i, (x1, y1, x2, y2) in enumerate(bounding_boxes):
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                cropped_plate = image[y1:y2, x1:x2]



                # 🔥 Görüntü iyileştirme uygula
                enhanced_plate_path = enhance_plate(cropped_plate)

                # 🔥 OCR işlemini çalıştır
                recognized_text = ocr_plate(enhanced_plate_path)
                print(f"OCR Sonucu: {recognized_text}")

                # 🔥 Ekrana yazdır
                ocr_result_label.config(text=f"OCR Result: {recognized_text}")

                # 🔥 Son işlenen plakayı ekranda göster
                show_result(enhanced_plate_path)

        else:
            ocr_result_label.config(text="No plates detected.")
    else:
        ocr_result_label.config(text="No image selected.")

# Sonuç görüntüsünü gösterme fonksiyonu
def show_result(output_path):
    if isinstance(output_path, str):
        img = Image.open(output_path)  # Eğer dosya yoluysa direkt aç
    else:
        img = Image.fromarray(output_path)  # Eğer numpy array ise, dönüştür

    # Pencere boyutlarını al
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    # Orijinal görüntü boyutlarını al
    img_width, img_height = img.size

    # En-boy oranını koruyarak yeni boyutları hesapla
    scale = min(window_width / img_width, (window_height - 100) / img_height)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)

    # Görüntüyü yeniden boyutlandır
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Tkinter için formatla
    img_tk = ImageTk.PhotoImage(img)

    # Canvas'ı pencerenin tamamına yay ve resmi ortaya yerleştir
    canvas.delete("all")
    canvas.config(width=window_width, height=window_height - 100)  # OCR sonucu için boşluk bırak
    canvas.create_image(window_width // 2, (window_height - 100) // 2, anchor='center', image=img_tk)
    canvas.image = img_tk  # Referans tutarak kaybolmasını engelle

# Arayüz elemanları
canvas = Canvas(root)
canvas.pack(expand=True, fill='both')

select_button = Button(root, text="Select Image", command=select_image)
select_button.pack(side='bottom', pady=20)

# Uygulamayı çalıştır
root.mainloop()
