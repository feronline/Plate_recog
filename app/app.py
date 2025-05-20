from flask import Flask, request, jsonify, send_from_directory
import os
import cv2
import psycopg2
from detection import detect_plates
from enhance import enhance_plate
from ocr import ocr_plate
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# --- PostgreSQL Bağlantısı ---
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD")
)
cursor = conn.cursor()

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    data = request.json
    plaka = data.get("plaka")
    marka = data.get("marka")
    model = data.get("model")
    renk = data.get("renk")
    yakit_turu = data.get("yakit_turu")
    arac_yili = int(data.get("arac_yili"))

    try:
        cursor.execute("SELECT * FROM vehicles WHERE plaka = %s;", (plaka,))
        if cursor.fetchone():
            return jsonify({"message": "Bu plaka zaten kayıtlı."}), 400

        cursor.execute("""
            INSERT INTO vehicles (plaka, marka, model, renk, yakit_turu, arac_yili)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (plaka, marka, model, renk, yakit_turu, arac_yili))
        conn.commit()
        return jsonify({"message": "Araç başarıyla kaydedildi."}), 200

    except Exception as e:
        conn.rollback()  # 🔴 BURASI EKLENDİ
        return jsonify({"error": f"İşleme sırasında hata: {str(e)}"}), 500


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "Dosya bulunamadı. Lütfen bir fotoğraf seçin."}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Geçersiz dosya. Lütfen bir fotoğraf seçin."}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        model_path = "../best.onnx"
        try:
            result_img, bounding_boxes = detect_plates(model_path, filepath)

            if result_img is not None and len(bounding_boxes) > 0:
                image = cv2.imread(filepath)
                for (x1, y1, x2, y2) in bounding_boxes:
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    cropped_plate = image[y1:y2, x1:x2]

                    enhanced_plate_path = enhance_plate(cropped_plate)
                    ocr_result = ocr_plate(enhanced_plate_path)

                    if not ocr_result:
                        continue  # boş sonuçsa atla

                    # Veritabanında plakayı ara
                    cursor.execute("SELECT * FROM vehicles WHERE plaka = %s;", (ocr_result,))
                    result = cursor.fetchone()

                    if result:
                        arac_data = {
                            "plaka": result[0],
                            "marka": result[1],
                            "model": result[2],
                            "renk": result[3],
                            "yakit_turu": result[4],
                            "arac_yili": result[5]
                        }
                        return jsonify({
                            "found": True,
                            "arac": arac_data
                        }), 200
                    else:
                        return jsonify({
                            "found": False,
                            "plaka": ocr_result
                        }), 200

            else:
                return jsonify({"error": "Plaka algılanamadı!"}), 400
        except Exception as e:
            return jsonify({"error": f"İşleme sırasında hata: {str(e)}"}), 500

    return jsonify({"error": "Bir hata oluştu. Lütfen tekrar deneyin."}), 500


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/static/results/<filename>')
def result_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
