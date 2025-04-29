from fastapi import APIRouter
from app.services.blockchain_service import get_balance
from app.services.tx_status_service import get_transaction_status
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Endereços conhecidos para teste em cada rede
NETWORK_TEST_ADDRESSES = {
    "mainnet": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Endereço do bloco gênesis
    "testnet": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"  # Endereço de teste padrão do Bitcoin Core
}

@router.get("/health")
async def health_check():
    health_status = {"status": "healthy", "networks": {}}
    
    try:
        # Verifica a conexão com mainnet e testnet
        for network in ["mainnet", "testnet"]:
            try:
                test_address = NETWORK_TEST_ADDRESSES[network]
                balance = get_balance(test_address, network, offline_mode=False)
                health_status["networks"][network] = {
                    "status": "ok",
                    "connection": "online"
                }
            except Exception as e:
                logger.warning(f"Erro ao verificar rede {network}: {str(e)}")
                health_status["networks"][network] = {
                    "status": "error",
                    "connection": "offline",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        return health_status
    except Exception as e:
        logger.error(f"Erro crítico ao verificar saúde do sistema: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/metrics")
async def metrics():
    try:
        metrics_data = {}
        
        # Coleta métricas para mainnet e testnet
        for network in ["mainnet", "testnet"]:
            try:
                address = NETWORK_TEST_ADDRESSES[network]
                balance = get_balance(address, network, offline_mode=False)
                
                metrics_data[network] = {
                    "confirmed_balance": balance.get("confirmed", 0),
                    "unconfirmed_balance": balance.get("unconfirmed", 0)
                }
            except Exception as e:
                logger.error(f"Erro ao coletar métricas para {network}: {str(e)}")
                metrics_data[network] = {
                    "error": str(e),
                    "confirmed_balance": 0,
                    "unconfirmed_balance": 0
                }
        
        return metrics_data
    except Exception as e:
        logger.error(f"Erro ao coletar métricas: {str(e)}")
        return {
            "error": str(e),
            "mainnet": {"confirmed_balance": 0, "unconfirmed_balance": 0},
            "testnet": {"confirmed_balance": 0, "unconfirmed_balance": 0}
        } 