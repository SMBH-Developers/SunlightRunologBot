from pathlib import Path

__all__ = ['DATA_DIR', 'PHOTOS_DIR', 'LOGS_DIR']

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
PHOTOS_DIR = DATA_DIR / "photos"
LOGS_DIR = DATA_DIR / "logs"
