from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / '.data'

os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/bitcoin_wallet.db"

CACHE_DIR = DATA_DIR / 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

KEYS_DIR = DATA_DIR / 'keys'
os.makedirs(KEYS_DIR, exist_ok=True)

LOGS_DIR = DATA_DIR / 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)
