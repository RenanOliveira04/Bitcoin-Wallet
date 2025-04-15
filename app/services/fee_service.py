import requests
import logging
import time
import random
from typing import Dict, Any
from app.models.fee_models import FeeEstimateModel

logger = logging.getLogger(__name__)

class FeeEstimator:
    """Serviço para estimativa de taxas de transação Bitcoin"""
    
    def __init__(self):
        self.fee_cache = {}
        self.cache_time = 0
        self.cache_duration = 300  # 5 minutos
    
    def _is_cache_valid(self) -> bool:
        """Verifica se o cache de taxas ainda é válido"""
        return (time.time() - self.cache_time) < self.cache_duration and self.fee_cache
    
    def estimate_from_mempool(self, network: str = "testnet") -> Dict[str, Any]:
        """
        Estima taxas com base nas condições atuais da mempool.
        
        Args:
            network: Rede Bitcoin ('testnet' ou 'mainnet')
            
        Returns:
            Dicionário com estimativas de taxas para diferentes prioridades
        """
        try:
            if self._is_cache_valid():
                logger.debug("Usando cache de taxas")
                return self.fee_cache
            
            if network == "mainnet":
                url = "https://mempool.space/api/v1/fees/recommended"
            else:
                url = "https://mempool.space/testnet/api/v1/fees/recommended"
            
            logger.info(f"Consultando taxas da mempool para rede {network}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            fee_data = response.json()
            
            result = {
                "fee_rate": fee_data.get("hourFee", 5), 
                "high_priority": fee_data.get("fastestFee", 10),  
                "medium_priority": fee_data.get("halfHourFee", 5),  
                "low_priority": fee_data.get("economyFee", 1),  
                "timestamp": int(time.time()),
                "unit": "sat/vB"
            }
            
            self.fee_cache = result
            self.cache_time = time.time()
            
            return result
        except Exception as e:
            logger.error(f"Erro ao obter taxas da mempool: {str(e)}", exc_info=True)
            return self._fallback_estimation(network)
    
    def _fallback_estimation(self, network: str) -> Dict[str, Any]:
        """Fornece uma estimativa de fallback quando as APIs falham"""
        base_fee = 5 if network == "mainnet" else 1
        
        high = max(1, base_fee * 2 + random.uniform(-0.5, 0.5))
        med = max(1, base_fee + random.uniform(-0.3, 0.3))
        low = max(0.5, base_fee / 2 + random.uniform(-0.1, 0.1))
        
        return {
            "fee_rate": med,
            "high_priority": high,
            "medium_priority": med,
            "low_priority": low,
            "timestamp": int(time.time()),
            "unit": "sat/vB",
            "source": "fallback"
        }

fee_estimator = FeeEstimator()

def get_fee_estimate(network: str = "testnet"):
    """
    Estima a taxa ideal para transações Bitcoin com base nas condições da rede.
    
    Esta função consulta APIs externas de estimativa de taxa para obter
    recomendações atualizadas para diferentes níveis de prioridade. As taxas
    são expressas em satoshis por byte virtual (sat/vB).
    
    Níveis de prioridade disponíveis:
    - Alta: Para transações urgentes (~10-20 minutos)
    - Média: Para transações normais (~1-3 blocos)
    - Baixa: Para transações não-urgentes (~6+ blocos)
    - Mínima: Taxa mínima para aceitação eventual
    
    Args:
        network (str, opcional): Rede Bitcoin ('mainnet' ou 'testnet').
            Padrão é "testnet".
    
    Returns:
        Dict: Estimativas de taxa contendo:
            - high (float): Taxa alta para confirmação rápida
            - medium (float): Taxa média para confirmação moderada
            - low (float): Taxa baixa para confirmação lenta
            - min (float): Taxa mínima aceitável
            - timestamp (int): Timestamp da estimativa
            - unit (str): Unidade da taxa (sat/vB)
        
    Raises:
        Exception: Se ocorrer um erro ao consultar a API de taxas
            (em caso de falha, valores de fallback são retornados)
    """
    fee_data = fee_estimator.estimate_from_mempool(network)
    high = fee_data['high_priority']
    medium = fee_data['medium_priority']
    low = fee_data['low_priority']
    min = fee_data['fee_rate']
    return FeeEstimateModel(
        high=high,
        medium=medium,
        low=low,
        min=min,
        timestamp=int(time.time()),
        unit="sat/vB"
    ) 