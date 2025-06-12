import cv2
import pytesseract
import re
import easyocr
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import time

reader = easyocr.Reader(['en'])
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-handwritten")
trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-handwritten")

ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def clean_text(text):
    return ''.join(c for c in text if c in ALLOWED_CHARS)

def is_valid_plate(text):
    return bool(re.match(r"^\d{2}[A-Z]{1,3}\d{2,5}$", text))

def score_plate(text):
    score = 0
    if is_valid_plate(text):
        score += 3
    if 6 <= len(text) <= 9:
        score += 1
    if text[:2].isdigit():
        score += 1
    if all(c in ALLOWED_CHARS for c in text):
        score += 1
    return score

def ocr_easy(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = reader.readtext(img_rgb, detail=0)
    return results[0].strip().upper() if results else ""

def ocr_trocr(img):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pixel_values = processor(images=img_pil, return_tensors="pt").pixel_values
    generated_ids = trocr_model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip().upper()

def ocr_tesseract_best(img):
    configs = [
        r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        r'--oem 3 --psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ]

    best_text = ""
    best_score = -1

    for config in configs:
        try:
            text = pytesseract.image_to_string(img, config=config).strip().upper()
            cleaned = clean_text(text)
            score = score_plate(cleaned)

            print(f"Tesseract ({config}) → {cleaned} [Skor: {score}]")

            if score > best_score:
                best_text = cleaned
                best_score = score
        except Exception as e:
            print(f"Tesseract ({config}) hata verdi: {e}")

    return best_text

def ocr_plate_multi(img):
    timings = {}

    # Tesseract
    start = time.time()
    tesseract_result = ocr_tesseract_best(img)
    timings["Tesseract"] = time.time() - start

    # EasyOCR
    start = time.time()
    easyocr_result = clean_text(ocr_easy(img))
    timings["EasyOCR"] = time.time() - start

    # TrOCR
    start = time.time()
    trocr_result = clean_text(ocr_trocr(img))
    timings["TrOCR"] = time.time() - start

    results = {
        "Tesseract": tesseract_result,
        "EasyOCR": easyocr_result,
        "TrOCR": trocr_result
    }

    scored = {k: (v, score_plate(v)) for k, v in results.items()}
    best = max(scored.items(), key=lambda x: x[1][1])

    print(f"OCR Karşılaştırması: {scored}")
    print(f"⏱️ Süreler (saniye): {timings}")

    return best[1][0]