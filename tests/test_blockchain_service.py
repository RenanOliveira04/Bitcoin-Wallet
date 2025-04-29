import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
import json
import os

sys.path.append(str(Path(__file__).parent.parent))

from app.services.blockchain_service import (
    get_balance, 
    get_utxos,
    PersistentBlockchainCache
)

class TestBlockchainService:
    """Testes unitários para o serviço de blockchain"""
    
    @pytest.fixture
    def mock_response(self):
        """Fixture para criar um mock de resposta HTTP"""
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {}
        return mock
    
    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Fixture para criar um diretório de cache temporário"""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        return str(cache_dir)
    
    def test_get_balance_online(self, mock_response):
        """Testa obtenção de saldo online"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        mock_response.json.return_value = {
            "chain_stats": {"funded_txo_sum": 1000000, "spent_txo_sum": 500000},
            "mempool_stats": {"funded_txo_sum": 200000, "spent_txo_sum": 0}
        }
        
        with patch("app.services.blockchain_service.requests.get") as mock_get, \
             patch.object(PersistentBlockchainCache, "get") as mock_cache_get, \
             patch.object(PersistentBlockchainCache, "set") as mock_cache_set:
            
            mock_get.return_value = mock_response
            mock_cache_get.return_value = None
            
            result = get_balance(address, network, offline_mode=False)
            
            mock_get.assert_called_once()
            assert f"testnet/api/address/{address}" in mock_get.call_args[0][0]
            
            assert result["confirmed"] == 500000  # 1000000 - 500000
            assert result["unconfirmed"] == 200000
            
            mock_cache_set.assert_called_once()
    
    def test_get_balance_offline(self):
        """Testa obtenção de saldo offline (do cache)"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        cache_data = {
            "confirmed": 500000,
            "unconfirmed": 200000
        }
        
        with patch.object(PersistentBlockchainCache, "get") as mock_cache_get, \
             patch("app.services.blockchain_service.requests.get") as mock_get:
            
            mock_cache_get.return_value = cache_data
            
            result = get_balance(address, network, offline_mode=True)
            
            mock_get.assert_not_called()
            
            assert result["confirmed"] == 500000
            assert result["unconfirmed"] == 200000
            
            mock_cache_get.assert_called()
    
    def test_get_utxos_online(self, mock_response):
        """Testa obtenção de UTXOs online"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        mock_utxos = [
            {
                "txid": "0000000000000000000000000000000000000000000000000000000000000001",
                "vout": 0,
                "status": {"confirmed": True},
                "value": 1000000
            },
            {
                "txid": "0000000000000000000000000000000000000000000000000000000000000002",
                "vout": 1,
                "status": {"confirmed": False},
                "value": 500000
            }
        ]
        
        mock_response.json.return_value = mock_utxos
        
        with patch("app.services.blockchain_service.requests.get") as mock_get, \
             patch.object(PersistentBlockchainCache, "get") as mock_cache_get, \
             patch.object(PersistentBlockchainCache, "set") as mock_cache_set:
            
            mock_get.return_value = mock_response
            mock_cache_get.return_value = None
            
            result = get_utxos(address, network, offline_mode=False)
            
            mock_get.assert_called_once()
            assert f"testnet/api/address/{address}/utxo" in mock_get.call_args[0][0]
            
            assert len(result) == 2
            assert result[0]["txid"] == "0000000000000000000000000000000000000000000000000000000000000001"
            assert result[0]["vout"] == 0
            assert result[0]["value"] == 1000000
            
            mock_cache_set.assert_called_once()
    
    def test_get_utxos_offline(self):
        """Testa obtenção de UTXOs offline (do cache)"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        utxos_data = [
            {
                "txid": "0000000000000000000000000000000000000000000000000000000000000001",
                "vout": 0,
                "value": 1000000,
                "confirmations": 6,
                "script": "0014000000000000000000000000000000000000"
            }
        ]
        
        with patch.object(PersistentBlockchainCache, "get") as mock_cache_get, \
             patch("app.services.blockchain_service.requests.get") as mock_get:
            
            mock_cache_get.return_value = utxos_data
            
            result = get_utxos(address, network, offline_mode=True)
            
            mock_get.assert_not_called()
            
            assert len(result) == 1
            assert result[0]["txid"] == "0000000000000000000000000000000000000000000000000000000000000001"
            assert result[0]["vout"] == 0
            assert result[0]["value"] == 1000000
            
            mock_cache_get.assert_called()
    
    def test_persistent_blockchain_cache(self, cache_dir):
        """Testa a classe PersistentBlockchainCache"""
        with patch("app.services.blockchain_service.get_cache_dir") as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(cache_dir)
            
            cache = PersistentBlockchainCache()
            
            test_key = "test_key"
            test_value = {"value": "test_value"}
            
            cache.set(test_key, test_value)
            retrieved_value = cache.get(test_key)
            
            assert retrieved_value == test_value
            
            cache_file = Path(cache_dir) / "blockchain_cache.json"
            assert cache_file.exists()
            
            with open(cache_file, 'r') as f:
                data = json.load(f)
                assert "cache" in data
                assert test_key in data["cache"]
                assert data["cache"][test_key] == test_value 