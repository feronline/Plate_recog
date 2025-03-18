import cv2
import pytesseract
import re

# OCR için Tesseract yolu
pytesseract.pytesseract.tesseract_cmd = r"C:\Tes\tesseract.exe"

# OCR hataları için düzeltme haritası (yalnızca harfler için)
OCR_CORRECTIONS = {
    "0": "O", "1": "I", "2": "Z", "5": "S", "8": "B"
}


def correct_ocr_errors(text, harf_sayisi):
    """OCR hatalarını düzeltir, ancak eğer harf grubu 3 harfse rakamları değiştirmez!"""
    corrected_text = ""
    letters_part = True  # Başlangıçta harf kısmındayız

    for c in text:
        if letters_part and c in OCR_CORRECTIONS:
            corrected_text += OCR_CORRECTIONS[c]  # Harf hatalarını düzelt
        else:
            if c.isdigit():
                letters_part = False  # Artık sayı kısmına geçtik
                if harf_sayisi == 3:
                    # Eğer harf grubu 3 harfse, rakamları değiştirme!
                    corrected_text += c
                    continue

            corrected_text += c  # Sayıları aynen bırak

    return corrected_text


def fix_plate_format(text):
    """OCR çıktısını düzelterek plaka formatına uygun hale getirir."""
    text = text.upper().replace("O", "0")  # O harfini 0 yap
    text = re.sub(r'[^A-Z0-9]', '', text)  # Geçersiz karakterleri temizle

    # İlk rakamdan başlamayan karakterleri temizle
    match = re.search(r'\d', text)
    if match:
        text = text[match.start():]
    else:
        return None  # Hiç rakam bulunamazsa geçersiz say

    # Plaka formatına uygun hale getirme
    pattern = re.match(r'(\d{2}) ?([A-Z]{1,3}) ?(\d+)', text)
    if pattern:
        city, letters, numbers = pattern.groups()

        # Eğer 3 harf varsa, sonrası sadece rakam olmalı
        if len(letters) == 3:
            numbers = re.sub(r'[^0-9]', '', numbers)  # Rakam olmayanları temizle

        fixed_plate = f"{city} {letters} {numbers}"
        return fixed_plate

    return None  # Format uymuyorsa boş döndür


def ocr_plate(img):
    """OCR işlemi yaparak plakadaki metni okur ve formatı doğrular."""

    # Eğer görüntü gri değilse griye çevir
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # OCR yapılandırması
    custom_config = r'--oem 3 --psm 9 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    # OCR çalıştır
    text = pytesseract.image_to_string(img, config=custom_config).strip()
    print(f"OCR RAW Output: {text}")  # Debug için OCR çıktısını yazdır

    # OCR çıktısını temizleyelim
    fixed_text = fix_plate_format(text)
    if not fixed_text:
        print("OCR sonucu plaka formatına uymuyor!")
        return None

    # Harf sayısını al
    parts = fixed_text.split()
    if len(parts) != 3:
        print("OCR sonucu plaka formatına uymuyor!")
        return None

    part1, part2, part3 = parts

    # OCR hatalarını düzelt
    part2 = correct_ocr_errors(part2, len(part2))

    # Yeni düzeltilmiş metin
    formatted_text = f"{part1} {part2} {part3}"

    # 📌 Plaka formatına uyup uymadığını kontrol et
    plate_pattern = [
        r"^\d{2} [A-Z] \d{4}$",  # 99 X 9999
        r"^\d{2} [A-Z] \d{5}$",  # 99 X 99999
        r"^\d{2} [A-Z]{2} \d{3}$",  # 99 XX 999
        r"^\d{2} [A-Z]{2} \d{4}$",  # 99 XX 9999
        r"^\d{2} [A-Z]{3} \d{2}$",  # 99 XXX 99
        r"^\d{2} [A-Z]{3} \d{3}$"  # 99 XXX 999
    ]

    if any(re.match(pattern, formatted_text) for pattern in plate_pattern):
        return formatted_text
    else:
        print("OCR sonucu plaka formatına uymuyor!")
        return None
