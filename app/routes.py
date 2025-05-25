from flask import request, redirect, url_for
from flask import render_template
import os
import cv2
from werkzeug.utils import secure_filename

from .detection import detect_plates
from .enhance import enhance_plate
from .ocr import ocr_plate_multi


def setup_routes(app):
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

    @app.route('/upload', methods=['POST'])
    def upload_image():
        if 'file' not in request.files:
            return "Dosya bulunamadı. Lütfen bir fotoğraf seçin."

        file = request.files['file']
        if file.filename == '':
            return "Geçersiz dosya. Lütfen bir fotoğraf seçin."

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # İşlemleri gerçekleştir
            model_path = "best.onnx"
            result_img, bounding_boxes = detect_plates(model_path, filepath)

            if result_img is not None and len(bounding_boxes) > 0:
                image = cv2.imread(filepath)

                for i, (x1, y1, x2, y2) in enumerate(bounding_boxes):
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    cropped_plate = image[y1:y2, x1:x2]

                    enhanced_plate_path = enhance_plate(cropped_plate)

                    ocr_result = ocr_plate_multi(enhanced_plate_path)
                    return f'''
                        <h1>OCR Sonucu: {ocr_result}</h1>
                        <h2>Yüklenen Görsel:</h2>
                        <img src="/static/uploads/{filename}" width="400">
                        <br><a href="/">Yeni fotoğraf yükle</a>
                    '''
            else:
                return "Plaka algılanamadı! <a href='/'>Yeni fotoğraf yükle</a>."

        return "Bir hata oluştu. Lütfen tekrar deneyin."
