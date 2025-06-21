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
    try:
        cursor.execute("SELECT * FROM vehicles WHERE plaka = %s;", (plaka,))
        if cursor.fetchone():
            return jsonify({"message": "Bu plaka zaten kayıtlı."}), 400

        cursor.execute("""
            INSERT INTO vehicles (plaka, marka, model, renk, yakit_turu, arac_yili, arac_tipi)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (plaka, marka, model, renk, yakit_turu, arac_yili, arac_tipi))
        conn.commit()
        return jsonify({"message": "Araç başarıyla kaydedildi."}), 200

    except Exception as e:
        conn.rollback()  # 🔴 BURASI EKLENDİ
        return jsonify({"error": f"İşleme sırasında hata: {str(e)}"}), 500


@app.route('/upload', methods=['POST'])
def upload_image():
    global_start = time.time()

    try:
        if 'file' not in request.files:
            return jsonify({"error": "Dosya bulunamadı."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Geçersiz dosya."}), 400

        file_start = time.time()
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        file_duration = time.time() - file_start

        detection_start = time.time()
        model_path = "../best.onnx"
        result_img, bounding_boxes = detect_plates(model_path, filepath)
        detection_duration = time.time() - detection_start

        if result_img is not None and len(bounding_boxes) > 0:
            image = cv2.imread(filepath)

            for (x1, y1, x2, y2) in bounding_boxes:
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                cropped_plate = image[y1:y2, x1:x2]

                enhance_start = time.time()
                enhanced_plate_path = enhance_plate(cropped_plate)
                enhance_duration = time.time() - enhance_start

                ocr_start = time.time()
                ocr_result = ocr_plate_multi(enhanced_plate_path)
                ocr_duration = time.time() - ocr_start

                if not ocr_result:
                    continue

                db_start = time.time()
                cursor.execute("SELECT * FROM vehicles WHERE plaka = %s;", (ocr_result,))
                result = cursor.fetchone()
                db_duration = time.time() - db_start

                # Marka tespiti

                detected_brand = detect_brand(filepath)
                print(f"🧠 Tespit edilen marka: {detected_brand}")

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
                    plate_queue.put(ocr_result)
                    response = jsonify({"found": True, "arac": arac_data}), 200
                else:
                    response = jsonify({"found": False, "plaka": ocr_result, "marka": detected_brand}), 200

                break
            else:
                response = jsonify({"error": "Plaka tespit edilemedi."}), 400
        else:
            response = jsonify({"error": "Plaka algılanamadı!"}), 400

    except Exception as e:
        print(f"🔥 Sunucu hatası: {e}")
        response = jsonify({"error": f"İşleme sırasında hata: {str(e)}"}), 500

    finally:
        total_duration = time.time() - global_start
        print(f"""
⏱️ Süreler:
- Dosya işlemleri:       {file_duration:.3f} sn
- Plaka tespiti:         {detection_duration:.3f} sn
- Görüntü iyileştirme:   {enhance_duration:.3f} sn
- OCR süresi:            {ocr_duration:.3f} sn
- Veritabanı sorgusu:    {db_duration:.3f} sn
- Toplam API süresi:     {total_duration:.3f} sn
""")

    return response

@app.route("/vehicle_logs", methods=["GET"])
def get_vehicle_log():
    plaka = request.args.get("plaka")  # ?plaka=... kısmını alır
    if not plaka:
        return jsonify({"error": "Plaka parametresi eksik"}), 400

    try:
        cursor.execute("SELECT * FROM vehicle_logs WHERE plate = %s;", (plaka,))
        result = cursor.fetchone()

        if result is None:
            return jsonify({"found": False, "message": "Kayıt bulunamadı."}), 200

        log_data = {
            "plaka": result[0],
            "entry_time": result[1].isoformat() if result[1] else None,
            "exit_time": result[2].isoformat() if result[2] else None,
            "total_time_seconds": result[3],
            "total_parked_seconds": result[4],
            "actual_moving_seconds": result[5],
            "carbon_emission": result[6]
        }

        return jsonify({"found": True, "log": log_data}), 200

    except Exception as e:
        print(f"❌ Log sorgu hatası: {e}")
        return jsonify({"error": "Sunucu hatası."}), 500




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