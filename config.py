import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret Key for session signing (configurable via env var)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'iiitv-ocms-spm-group37-secret-key-2026')

    # Database URI: checks DATABASE_URL, with postgres:// fix for SQLAlchemy 2.0+
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{os.path.join(BASE_DIR, 'ocms.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads folder (configurable for Render persistent disk or local fallback)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
