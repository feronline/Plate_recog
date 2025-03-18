import re

def format_plate_text(ocr_text):
    # Küçük harfleri büyüğe çevir, boşlukları temizle
    ocr_text = ocr_text.strip().upper().replace(" ", "")

    # OCR hatalarını düzeltmeye yönelik dönüşümler
    replacements = {
        "O": "0",  # O harfini sıfıra çevir
        "I": "1",  # I harfini bire çevir
        "Z": "2",  # Z harfini ikiye çevir
    }
    for wrong, correct in replacements.items():
        ocr_text = ocr_text.replace(wrong, correct)

    # İlk rakamın bulunduğu noktayı tespit et
    first_digit_index = next((i for i, c in enumerate(ocr_text) if c.isdigit()), None)

    # Eğer hiç rakam yoksa geçersiz say
    if first_digit_index is None:
        return "Geçersiz plaka"

    # İlk rakamdan itibaren olan kısmı al
    ocr_text = ocr_text[first_digit_index:]

    # Plaka formatlarını tanımlayan regex desenleri
    plate_patterns = [
        r"^(\d{2})[ ]?([A-Z]{1})[ ]?(\d{4,5})$",  # 99 X 9999, 99 X 99999
        r"^(\d{2})[ ]?([A-Z]{2})[ ]?(\d{3,4})$",  # 99 XX 999, 99 XX 9999
        r"^(\d{2})[ ]?([A-Z]{3})[ ]?(\d{2,3})$",  # 99 XXX 99, 99 XXX 999
    ]

    for pattern in plate_patterns:
        match = re.match(pattern, ocr_text)
        if match:
            return f"{match.group(1)} {match.group(2)} {match.group(3)}"  # Plaka düzenini koru

    return "Geçersiz plaka"


