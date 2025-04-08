from flask import Flask
import os


def create_app():
    app = Flask(__name__)

    # Statik klasörleri ayarla
    UPLOAD_FOLDER = 'app/static/uploads'
    RESULT_FOLDER = 'app/static/results'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['RESULT_FOLDER'] = RESULT_FOLDER

    # Tüm route'ları buradan içe aktar
    from .routes import setup_routes
    setup_routes(app)

    return app
