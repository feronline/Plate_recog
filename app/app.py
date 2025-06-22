from flask import Flask, request, jsonify, send_from_directory
import os
import cv2
import psycopg2
from detection import detect_plates
from enhance import enhance_plate
from ocr import ocr_plate_multi
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import time
from brand_detector import detect_brand

load_dotenv()
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
plate_queue = None
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

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
    arac_tipi = data.get("arac_tipi")

    cursor.execute("SELECT * FROM vehicles WHERE plaka = %s;", (plaka,))
    if cursor.fetchone():
        return jsonify({"message": "Bu plaka zaten kayıtlı."}), 400

    cursor.execute("""
        INSERT INTO vehicles (plaka, marka, model, renk, yakit_turu, arac_yili, arac_tipi)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, (plaka, marka, model, renk, yakit_turu, arac_yili, arac_tipi))
    conn.commit()
    return jsonify({"message": "Araç başarıyla kaydedildi."}), 200


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "Dosya bulunamadı."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Geçersiz dosya."}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    model_path = "../best.onnx"
    result_img, bounding_boxes = detect_plates(model_path, filepath)

    if result_img is not None and len(bounding_boxes) > 0:
        image = cv2.imread(filepath)

        for (x1, y1, x2, y2) in bounding_boxes:
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            cropped_plate = image[y1:y2, x1:x2]

            enhanced_plate_path = enhance_plate(cropped_plate)
            ocr_result = ocr_plate_multi(enhanced_plate_path)

            if not ocr_result:
                continue

            cursor.execute("SELECT * FROM vehicles WHERE plaka = %s;", (ocr_result,))
            result = cursor.fetchone()
            detected_brand = detect_brand(filepath)

            if result:
                arac_data = {
                    "plaka": result[0],
                    "marka": detected_brand if result[1] is None or result[1] == "unknown" else result[1],
                    "model": result[2],
                    "renk": result[3],
                    "yakit_turu": result[4],
                    "arac_yili": result[5],
                    "arac_tipi": result[6],
                    "karbon_emisyon": result[7]
                }
                if plate_queue:
                    plate_queue.put(ocr_result)
                return jsonify({"found": True, "arac": arac_data}), 200
            else:
                return jsonify({"found": False, "plaka": ocr_result, "marka": detected_brand}), 200

        return jsonify({"error": "Plaka tespit edilemedi."}), 400
    else:
        return jsonify({"error": "Plaka algılanamadı!"}), 400


@app.route("/vehicle_logs", methods=["GET"])
def get_all_vehicle_logs():
    try:
        cursor.execute("SELECT * FROM vehicle_logs;")
        results = cursor.fetchall()

        if not results:
            return jsonify({"found": False, "message": "Kayıt bulunamadı."}), 200

        logs = []
        for result in results:
            logs.append({
                "plaka": result[0],
                "entry_time": result[1].isoformat() if result[1] else None,
                "exit_time": result[2].isoformat() if result[2] else None,
                "total_time_seconds": result[3],
                "total_parked_seconds": result[4],
                "actual_moving_seconds": result[5],
                "carbon_emission": result[6]
            })

        return jsonify({"found": True, "logs": logs}), 200

    except Exception as e:
        print(f"❌ Tüm logları çekme hatası: {e}")
        return jsonify({"error": "Sunucu hatası."}), 500


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/static/results/<filename>')
def result_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)


def run_with_queue(queue):
    global plate_queue
    plate_queue = queue
    app.run(host="0.0.0.0", port=5000)
