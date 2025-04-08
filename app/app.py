from flask import Flask, request, redirect, url_for
import os
import cv2
from app.detection import detect_plates
from app.enhance import enhance_plate
from app.ocr import ocr_plate
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Fotoğrafların yükleneceği klasör
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


# Ana sayfa - Fotoğraf yükleme formu
@app.route('/')
def upload_form():
    return '''
        <h1>Plaka Algılama ve OCR</h1>
        <form method="post" action="/upload" enctype="multipart/form-data">
            <label>Bir fotoğraf seçin:</label>
            <input type="file" name="file">
            <button type="submit">Yükle ve İşle</button>
        </form>
    '''


# Fotoğrafı işleyen view
@app.route('/upload', methods=['POST'])
def upload_image():
    # Kullanıcıdan gelen dosya
    if 'file' not in request.files:
        return "Dosya bulunamadı. Lütfen bir fotoğraf seçin."

    file = request.files['file']

    if file.filename == '':
        return "Geçersiz dosya. Lütfen bir fotoğraf seçin."

    if file:
        # Yüklenen dosyayı güvenli bir şekilde kaydet
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # İşlemleri gerçekleştir
        model_path = "../best.onnx"
        result_img, bounding_boxes = detect_plates(model_path, filepath)

        if result_img is not None and len(bounding_boxes) > 0:
            # İlk bulunan plakayı OCR işlemi için alıyoruz
            image = cv2.imread(filepath)

            for i, (x1, y1, x2, y2) in enumerate(bounding_boxes):
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                cropped_plate = image[y1:y2, x1:x2]

                # Görüntüyü iyileştir
                enhanced_plate_path = enhance_plate(cropped_plate)

                # OCR ile plaka tanıma
                ocr_result = ocr_plate(enhanced_plate_path)

                # Sonucu ekrana yazdır
                return f'''
                    <h1>OCR Sonucu: {ocr_result}</h1>
                    <h2>Yüklenen Görsel:</h2>
                    <img src="/static/uploads/{filename}" width="400">
                    <br><a href="/">Yeni fotoğraf yükle</a>
                '''
        else:
            return "Plaka algılanamadı! <a href='/'>Yeni fotoğraf yükle</a>."

    return "Bir hata oluştu. Lütfen tekrar deneyin."



# Yüklenen ve işlenen dosyaları statik olarak servis et
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for('uploaded_file', filename=filename))


@app.route('/static/results/<filename>')
def result_file(filename):
    return redirect(url_for('result_file', filename=filename))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
