from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import keys, addresses, balance, utxo, broadcast, fee, sign, validate, tx
from app.dependencies import get_network, setup_logging, get_settings
import logging

# Inicializa o logger com as configurações do .env
logger = setup_logging()
settings = get_settings()

app = FastAPI(
    title="Bitcoin Wallet API",
    version="1.0.0",
    description="API para gerenciamento de carteiras Bitcoin, suportando diferentes formatos de endereços e operações com transações."
)

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
app.include_router(fee.router, prefix="/api/fee")
app.include_router(sign.router, prefix="/api/sign")
app.include_router(validate.router, prefix="/api/validate")
app.include_router(tx.router, prefix="/api/tx")

# Health check
@app.get("/")
def read_root():
    logger.info("Health check realizado")
    return {
        "status": "running",
        "network": get_network(),
        "default_key_type": settings.default_key_type,
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    """Executado quando a aplicação inicia"""
    logger.info(f"Iniciando API Bitcoin Wallet na rede {get_network()}")
    logger.info(f"Tipo de chave padrão: {settings.default_key_type}")
    
    # Logar apenas a informação de que as URLs estão configuradas, sem expor os valores
    if settings.blockchain_api_url:
        logger.info("Blockchain API URL configurada")
    else:
        logger.warning("Blockchain API URL não configurada - usando valor padrão")
        
    if settings.mempool_api_url:
        logger.info("Mempool API URL configurada")
    else:
        logger.warning("Mempool API URL não configurada - usando valor padrão")
        
    # Verificar configurações de API
    if settings.api_key:
        logger.info("API Key configurada")
    
    logger.info(f"Nível de log: {settings.log_level}")
    logger.info(f"Tempo de cache: {settings.cache_timeout} segundos")