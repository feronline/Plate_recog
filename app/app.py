from flask import Flask, request, jsonify, send_from_directory
import os
import cv2
from detection import detect_plates
from enhance import enhance_plate
from ocr import ocr_plate
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


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
                plates = []
                image = cv2.imread(filepath)
                for i, (x1, y1, x2, y2) in enumerate(bounding_boxes):
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    cropped_plate = image[y1:y2, x1:x2]

                    enhanced_plate_path = enhance_plate(cropped_plate)
                    ocr_result = ocr_plate(enhanced_plate_path)

                    plates.append({
                        "plate_number": ocr_result,
                        "bounding_box": [x1, y1, x2, y2]
                    })

                result_filename = f'processed_{filename}'
                result_filepath = os.path.join(app.config['RESULT_FOLDER'], result_filename)
                cv2.imwrite(result_filepath, result_img)

                return jsonify({
                    "message": "Plaka başarıyla algılandı.",
                    "original_image": f"/static/uploads/{filename}",
                    "processed_image": f"/static/results/{result_filename}",
                    "plates": plates
                }), 200

            else:
                return jsonify({"error": "Plaka algılanamadı!"}), 400
        except Exception as e:
            return jsonify({"error": f"İşleme sırasında bir hata oluştu: {str(e)}"}), 500

    return jsonify({"error": "Bir hata oluştu. Lütfen tekrar deneyin."}), 500


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/static/results/<filename>')
def result_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
