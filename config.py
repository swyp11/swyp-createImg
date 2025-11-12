import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

load_dotenv()

ROOT_DIR = Path(__file__).parent

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("DB_USER, DB_PASSWORD, and DB_NAME must be set in environment variables")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

def get_db_engine():
    return create_engine(DATABASE_URL, poolclass=NullPool, echo=False)

DB_TABLES = {
    'tb_dress': {
        'table_name': 'tb_dress',
        'prompt_fields': ['name', 'type', 'color', 'shape', 'mood', 'neck_line', 'fabric', 'features'],
        'prompt_template': 'wedding_dress'
    },
    'tb_dress_shop': {
        'table_name': 'tb_dress_shop',
        'prompt_fields': ['shop_name', 'description', 'features', 'specialty'],
        'prompt_template': 'wedding_dress_shop'
    },
    'tb_wedding_hall': {
        'table_name': 'tb_wedding_hall',
        'prompt_fields': ['name', 'venue_type', 'parking'],
        'prompt_template': 'wedding_hall'
    },
    'tb_makeup_shop': {
        'table_name': 'tb_makeup_shop',
        'prompt_fields': ['shop_name', 'description', 'features', 'specialty'],
        'prompt_template': 'makeup_shop'
    }
}

SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = int(os.getenv('SSH_PORT', 22))
SSH_USER = os.getenv('SSH_USER')
SSH_PASSWORD = os.getenv('SSH_PASSWORD')

SERVER_IMAGE_PATH = os.getenv('SERVER_IMAGE_PATH', '/data/images')
IMAGE_URL_BASE = os.getenv('IMAGE_URL_BASE', '/images')

IMAGE_SIZE = os.getenv('IMAGE_SIZE', '512x512')
IMAGE_QUALITY = os.getenv('IMAGE_QUALITY', 'standard')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
DEFAULT_GENERATION_LIMIT = os.getenv('DEFAULT_GENERATION_LIMIT')
DEFAULT_GENERATION_LIMIT = int(DEFAULT_GENERATION_LIMIT) if DEFAULT_GENERATION_LIMIT else None

OUTPUT_DIR = ROOT_DIR / 'generated_images'
OUTPUT_DIR.mkdir(exist_ok=True)
