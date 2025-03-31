from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import keys, addresses, balance, utxo, broadcast
from app.dependencies import get_network
import logging
import logging.config

# Configuração de logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "bitcoin-wallet.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "INFO"
        }
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO"
    }
})

logger = logging.getLogger(__name__)

app = FastAPI(title="Bitcoin Wallet API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(keys.router, prefix="/api/keys")
app.include_router(addresses.router, prefix="/api/addresses")
app.include_router(balance.router, prefix="/api/balance")
app.include_router(utxo.router, prefix="/api/utxo")
app.include_router(broadcast.router, prefix="/api/broadcast")

# Health check
@app.get("/")
def read_root():
    logger.info("Health check realizado")
    return {"status": "running", "network": get_network()}