from fastapi import APIRouter
from app.services.blockchain_service import get_balance
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

NETWORK_TEST_ADDRESSES = {
    "mainnet": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  
    "testnet": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx" 
}

@router.get("/health")
async def health_check():
    health_status = {"status": "healthy", "networks": {}}
    error_count = 0
    total_networks = len(["mainnet", "testnet"])
    
    try:
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
                error_count += 1
        
        if error_count == total_networks:
            health_status["status"] = "unhealthy"
            health_status["error"] = "Todas as redes estão inacessíveis"
        elif error_count > 0:
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
        error_occurred = False
        
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
                error_occurred = True
                metrics_data[network] = {
                    "error": str(e),
                    "confirmed_balance": 0,
                    "unconfirmed_balance": 0
                }
        
        if error_occurred:
            metrics_data["error"] = "Erro ao coletar algumas métricas"
        
        return metrics_data
    except Exception as e:
        logger.error(f"Erro ao coletar métricas: {str(e)}")
        return {
            "error": str(e),
            "mainnet": {"confirmed_balance": 0, "unconfirmed_balance": 0},
            "testnet": {"confirmed_balance": 0, "unconfirmed_balance": 0}
        } 