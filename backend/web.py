from pathlib import Path
from fastapi.staticfiles import StaticFiles
def serve_web(app):
    dist = Path(__file__).resolve().parents[1] / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist, html=True), name='web')
