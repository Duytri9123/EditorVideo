# app/routes/init.py
from .health import health_bp
from .download import download_bp
from .timeline import timeline_bp
from .clips import clips_bp
from .processing import processing_bp
from .upload import upload_bp
from .files import files_bp
from .effects import effects_bp

def register_routes(app, video_service):
    """Register all blueprints with the app"""
    blueprints = [
        (health_bp, '/api'),
        (download_bp, '/api'),
        (timeline_bp, '/api'),
        (clips_bp, '/api'),
        (processing_bp, '/api'),
        (upload_bp, '/api'),
        (files_bp, '/api'),
        (effects_bp, '/api')
    ]

    for bp, url_prefix in blueprints:
        bp.video_service = video_service
        app.register_blueprint(bp, url_prefix=url_prefix)