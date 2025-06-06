from flask import Flask
from flask_cors import CORS  # 导入 Flask-CORS

def create_app():
    app = Flask(__name__,static_folder='static', template_folder='templates')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # 初始化 Flask-CORS，允许跨域请求
    CORS(app, resources={r"/*": {"origins": "*"}})

    from .routes import main
    app.register_blueprint(main)

    return app