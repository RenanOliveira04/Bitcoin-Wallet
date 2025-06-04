import requests
import logging
import time
import random
from typing import Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)

class FeeEstimation(TypedDict):
    high: float
    medium: float
    low: float
    min: float
    timestamp: int
    unit: str
    source: str

class FeeAPI(TypedDict):
    name: str
    url: str
    parser: callable
    timeout: int
    priority: int

class FeeEstimator:
    def __init__(self, cache_duration: int = 300):
        self.cache_duration = cache_duration
        self._last_update: Dict[str, float] = {}
        self._cache: Dict[str, FeeEstimation] = {}
    
    def _get_cache_key(self, network: str) -> str:
        return f"fee_estimate_{network}"
    
    def _is_cache_valid(self, network: str) -> bool:
        cache_key = self._get_cache_key(network)
        last_update = self._last_update.get(cache_key, 0)
        return (time.time() - last_update) < self.cache_duration and cache_key in self._cache
    
    def _update_cache(self, network: str, data: FeeEstimation):
        cache_key = self._get_cache_key(network)
        self._cache[cache_key] = data
        self._last_update[cache_key] = time.time()
    
    def _get_cached_estimate(self, network: str) -> Optional[FeeEstimation]:
        cache_key = self._get_cache_key(network)
        return self._cache.get(cache_key)
    
    def _get_fee_apis(self, network: str) -> List[FeeAPI]:
        base_url = "testnet/api" if network == "testnet" else "api"
        return [
            {
                "name": "mempool.space",
                "url": f"https://mempool.space/{base_url}/v1/fees/recommended",
                "parser": self._parse_mempool_response,
                "timeout": 5,
                "priority": 1
            },
            {
                "name": "blockstream.info",
                "url": f"https://blockstream.info/{base_url}/fee-estimates",
                "parser": self._parse_blockstream_response,
                "timeout": 5,
                "priority": 2
            },
            {
                "name": "blockcypher.com",
                "url": f"https://api.blockcypher.com/v1/btc/{'test3' if network == 'testnet' else 'main'}",
                "parser": self._parse_blockcypher_response,
                "timeout": 5,
                "priority": 3
            }
        ]
    
    def _parse_mempool_response(self, data: Dict) -> FeeEstimation:
        return {
            "high": data.get("fastestFee", 20),
            "medium": data.get("halfHourFee", 10),
            "low": data.get("hourFee", 5),
            "min": data.get("minimumFee", 1),
            "timestamp": int(time.time()),
            "unit": "sat/vB",
            "source": "mempool.space"
        }
    
    def _parse_blockstream_response(self, data: Dict) -> FeeEstimation:
        return {
            "high": int(data.get("2", 20)),
            "medium": int(data.get("6", 10)),
            "low": int(data.get("12", 5)),
            "min": 1,
            "timestamp": int(time.time()),
            "unit": "sat/vB",
            "source": "blockstream.info"
        }
    
    def _parse_blockcypher_response(self, data: Dict) -> FeeEstimation:
        return {
            "high": data.get("high_fee_per_kb", 20000) // 1000,  
            "medium": data.get("medium_fee_per_kb", 10000) // 1000,
            "low": data.get("low_fee_per_kb", 5000) // 1000,
            "min": 1,
            "timestamp": int(time.time()),
            "unit": "sat/vB",
            "source": "blockcypher.com"
        }
    
    def _get_fallback_estimation(self, network: str) -> FeeEstimation:
        base_fee = 5 if network == "mainnet" else 1
        return {
            "high": max(1, base_fee * 2 + random.uniform(-0.5, 0.5)),
            "medium": max(1, base_fee + random.uniform(-0.3, 0.3)),
            "low": max(0.5, base_fee / 2 + random.uniform(-0.1, 0.1)),
            "min": 1,
            "timestamp": int(time.time()),
            "unit": "sat/vB",
            "source": "fallback"
        }
    
    def get_fee_estimate(self, network: str = "testnet") -> FeeEstimation:
        if self._is_cache_valid(network):
            return self._get_cached_estimate(network)
        
        apis = self._get_fee_apis(network)
        last_error = None
        
        for api in sorted(apis, key=lambda x: x["priority"]):
            try:
                logger.info(f"[FEE] Trying {api['name']} for {network} fees")
                response = requests.get(api['url'], timeout=api['timeout'])
                response.raise_for_status()
                
                result = api['parser'](response.json())
                self._update_cache(network, result)
                logger.info(f"[FEE] Successfully got fees from {api['name']}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"[FEE] Failed to get fees from {api['name']}: {str(e)}")
                continue
        
        logger.warning("[FEE] All fee APIs failed, using fallback")
        fallback = self._get_fallback_estimation(network)
        self._update_cache(network, fallback)
        return fallback

fee_estimator = FeeEstimator()

def get_fee_estimate(network: str = "testnet") -> FeeEstimation:
    """
    Get fee estimates for the specified network.
    
    Args:
        network: Bitcoin network ('mainnet' or 'testnet')
        
    Returns:
        FeeEstimation: Fee estimates with different priorities
    """
    try:
        fees = fee_estimator.get_fee_estimate(network)
        return FeeEstimateModel(
            high=fees["high"],
            medium=fees["medium"],
            low=fees["low"],
            min=fees["min"],
            timestamp=fees["timestamp"],
            unit=fees["unit"]
        )
    except Exception as e:
        logger.error(f"[FEE] Error getting fee estimate: {str(e)}")
        return FeeEstimateModel(
            high=20,
            medium=10,
            low=5,
            min=1,
            timestamp=int(time.time()),
            unit="sat/vB"
        )