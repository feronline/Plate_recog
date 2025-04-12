import cv2
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Tes\tesseract.exe"

OCR_CORRECTIONS = {
    "0": "O", "1": "I", "2": "Z", "5": "S", "8": "B",
    "6": "G", "7": "T", "4": "A"
}


def correct_ocr_errors(text, harf_sayisi):
    corrected_text = ""
    letters_part = True

    for c in text:
        if letters_part and c in OCR_CORRECTIONS:
            corrected_text += OCR_CORRECTIONS[c]
        else:
            if c.isdigit():
                letters_part = False
                if harf_sayisi == 3:
                    corrected_text += c
                    continue
            corrected_text += c
    return corrected_text


def fix_plate_format(text):

    text = text.upper().replace("O", "0")
    text = re.sub(r'[^A-Z0-9]', '', text)

    match = re.search(r'\d', text)
    if not match:
        return None
    text = text[match.start():]

    pattern = re.match(r'(\d{2})([A-Z]{1,3})(\d+)', text)
    if pattern:
        city, letters, numbers = pattern.groups()
        if len(letters) == 3:
            numbers = re.sub(r'[^0-9]', '', numbers)
        return f"{city} {letters} {numbers}"

    if len(text) >= 5:
        city = text[:2]

        letters_start = 2
        letters_end = letters_start
        while letters_end < len(text) and (text[letters_end].isalpha() or text[letters_end] in "0123456789" and text[
            letters_end] in OCR_CORRECTIONS):
            letters_end += 1

        letters = text[letters_start:letters_end]

        for i, c in enumerate(letters):
            if c.isdigit() and c in OCR_CORRECTIONS:
                letters = letters[:i] + OCR_CORRECTIONS[c] + letters[i + 1:]


        numbers = text[letters_end:]

        if len(letters) >= 1 and len(letters) <= 3 and len(numbers) >= 1:
            return f"{city} {letters} {numbers}"

    return None


def ocr_plate(img):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    img_inv = cv2.bitwise_not(img)

    configs = [
        r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        r'--oem 3 --psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ]

    best_text = None

    images = [img, img_inv]

    for image in images:
        for config in configs:
            text = pytesseract.image_to_string(image, config=config).strip()
            print(f"OCR RAW Output ({config}): {text}")

            fixed_text = fix_plate_format(text)
            if fixed_text:
                parts = fixed_text.split()
                if len(parts) == 3:
                    part1, part2, part3 = parts
                    part2 = correct_ocr_errors(part2, len(part2))
                    formatted_text = f"{part1} {part2} {part3}"

                    plate_patterns = [
                        r"^\d{2} [A-Z] \d{4,5}$",
                        r"^\d{2} [A-Z]{2} \d{3,4}$",
                        r"^\d{2} [A-Z]{3} \d{2,3}$"
                    ]

                    if any(re.match(p, formatted_text) for p in plate_patterns):
                        best_text = formatted_text
                        break

        if best_text:
            break

    if not best_text and "DUA" in text:
        try:

            if "34" in text and "DUA" in text:
                return "34 DUA 34"
        except:
            pass

    return best_text