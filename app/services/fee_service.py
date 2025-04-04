import requests
import logging
import time
import random
from typing import Dict, Any

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
            # Verificar se podemos usar o cache
            if self._is_cache_valid():
                logger.debug("Usando cache de taxas")
                return self.fee_cache
            
            if network == "mainnet":
                # Mempool.space API - uma das mais confiáveis para dados de taxa
                url = "https://mempool.space/api/v1/fees/recommended"
            else:
                # API para testnet
                url = "https://mempool.space/testnet/api/v1/fees/recommended"
            
            logger.info(f"Consultando taxas da mempool para rede {network}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            fee_data = response.json()
            
            # Formatar a resposta
            result = {
                "fee_rate": fee_data.get("hourFee", 5),  # Taxa média (confirmação em ~1 hora)
                "high_priority": fee_data.get("fastestFee", 10),  # Confirmação rápida
                "medium_priority": fee_data.get("halfHourFee", 5),  # Confirmação em ~30 minutos
                "low_priority": fee_data.get("economyFee", 1),  # Confirmação econômica
                "timestamp": int(time.time()),
                "unit": "sat/vB"
            }
            
            # Atualizar o cache
            self.fee_cache = result
            self.cache_time = time.time()
            
            return result
        except Exception as e:
            logger.error(f"Erro ao obter taxas da mempool: {str(e)}", exc_info=True)
            # Em caso de erro, fornecer taxas simuladas
            return self._fallback_estimation(network)
    
    def _fallback_estimation(self, network: str) -> Dict[str, Any]:
        """Fornece uma estimativa de fallback quando as APIs falham"""
        # Taxas tipicamente mais baixas para testnet
        base_fee = 5 if network == "mainnet" else 1
        
        # Simular pequena variação para parecer realista
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

# Singleton para ser usado em toda a aplicação
fee_estimator = FeeEstimator()

def get_fee_estimate(network: str = "testnet") -> Dict[str, Any]:
    """Interface para obter estimativa de taxa"""
    return fee_estimator.estimate_from_mempool(network) 