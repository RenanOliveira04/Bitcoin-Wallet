import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
import json
import os

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.services.blockchain_service import (
    get_balance, 
    get_utxos, 
    broadcast_transaction,
    get_transaction_info,
    ensure_cache_dir,
    check_connection,
    save_to_cache,
    load_from_cache
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
        
        # Mock para a API Blockstream
        mock_response.json.return_value = {
            "chain_stats": {"funded_txo_sum": 1000000, "spent_txo_sum": 500000},
            "mempool_stats": {"funded_txo_sum": 200000, "spent_txo_sum": 0}
        }
        
        with patch("app.services.blockchain_service.requests.get") as mock_get, \
             patch("app.services.blockchain_service.ensure_cache_dir") as mock_ensure_cache_dir, \
             patch("app.services.blockchain_service.save_to_cache") as mock_save_to_cache:
            
            mock_get.return_value = mock_response
            mock_ensure_cache_dir.return_value = "/tmp/cache"
            
            result = get_balance(address, network, offline_mode=False)
            
            # Verificar chamada à API
            mock_get.assert_called_once()
            assert f"testnet/api/address/{address}" in mock_get.call_args[0][0]
            
            # Verificar cálculo do saldo
            assert result["confirmed"] == 500000  # 1000000 - 500000
            assert result["unconfirmed"] == 200000
            
            # Verificar salvamento no cache
            mock_save_to_cache.assert_called_once()
    
    def test_get_balance_offline(self, cache_dir):
        """Testa obtenção de saldo offline (do cache)"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        # Criar um cache de teste
        cache_data = {
            "balance_testnet_tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx": {
                "confirmed": 500000,
                "unconfirmed": 200000
            }
        }
        
        with patch("app.services.blockchain_service.ensure_cache_dir") as mock_ensure_cache_dir, \
             patch("app.services.blockchain_service.load_from_cache") as mock_load_from_cache, \
             patch("app.services.blockchain_service.requests.get") as mock_get:
            
            mock_ensure_cache_dir.return_value = cache_dir
            mock_load_from_cache.return_value = cache_data
            
            result = get_balance(address, network, offline_mode=True)
            
            # Verificar que não houve chamada à API
            mock_get.assert_not_called()
            
            # Verificar saldo do cache
            assert result["confirmed"] == 500000
            assert result["unconfirmed"] == 200000
            
            # Verificar cache foi carregado
            mock_load_from_cache.assert_called_once()
    
    def test_get_utxos_online(self, mock_response):
        """Testa obtenção de UTXOs online"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        # Mock para a API Blockstream
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
             patch("app.services.blockchain_service.ensure_cache_dir") as mock_ensure_cache_dir, \
             patch("app.services.blockchain_service.save_to_cache") as mock_save_to_cache:
            
            mock_get.return_value = mock_response
            mock_ensure_cache_dir.return_value = "/tmp/cache"
            
            result = get_utxos(address, network, offline_mode=False)
            
            # Verificar chamada à API
            mock_get.assert_called_once()
            assert f"testnet/api/address/{address}/utxo" in mock_get.call_args[0][0]
            
            # Verificar UTXOs retornados
            assert len(result) == 2
            assert result[0]["txid"] == "0000000000000000000000000000000000000000000000000000000000000001"
            assert result[0]["vout"] == 0
            assert result[0]["value"] == 1000000
            assert result[0]["confirmations"] > 0
            
            assert result[1]["txid"] == "0000000000000000000000000000000000000000000000000000000000000002"
            assert result[1]["vout"] == 1
            assert result[1]["value"] == 500000
            assert result[1]["confirmations"] == 0
            
            # Verificar salvamento no cache
            mock_save_to_cache.assert_called_once()
    
    def test_get_utxos_offline(self, cache_dir):
        """Testa obtenção de UTXOs offline (do cache)"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        network = "testnet"
        
        # Criar um cache de teste
        utxos_data = [
            {
                "txid": "0000000000000000000000000000000000000000000000000000000000000001",
                "vout": 0,
                "value": 1000000,
                "confirmations": 6,
                "script": "0014000000000000000000000000000000000000"
            }
        ]
        
        cache_data = {
            "utxos_testnet_tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx": utxos_data
        }
        
        with patch("app.services.blockchain_service.ensure_cache_dir") as mock_ensure_cache_dir, \
             patch("app.services.blockchain_service.load_from_cache") as mock_load_from_cache, \
             patch("app.services.blockchain_service.requests.get") as mock_get:
            
            mock_ensure_cache_dir.return_value = cache_dir
            mock_load_from_cache.return_value = cache_data
            
            result = get_utxos(address, network, offline_mode=True)
            
            # Verificar que não houve chamada à API
            mock_get.assert_not_called()
            
            # Verificar UTXOs do cache
            assert len(result) == 1
            assert result[0]["txid"] == "0000000000000000000000000000000000000000000000000000000000000001"
            assert result[0]["vout"] == 0
            assert result[0]["value"] == 1000000
            
            # Verificar cache foi carregado
            mock_load_from_cache.assert_called_once()
    
    def test_broadcast_transaction(self, mock_response):
        """Testa broadcast de transação"""
        tx_hex = "0100000001010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101"
        network = "testnet"
        
        # Mock para a API Blockstream
        mock_response.text = "0000000000000000000000000000000000000000000000000000000000000001"
        
        with patch("app.services.blockchain_service.requests.post") as mock_post:
            mock_post.return_value = mock_response
            
            result = broadcast_transaction(tx_hex, network)
            
            # Verificar chamada à API
            mock_post.assert_called_once()
            assert f"testnet/api/tx" in mock_post.call_args[0][0]
            
            # Verificar TXID retornado
            assert result == "0000000000000000000000000000000000000000000000000000000000000001"
    
    def test_get_transaction_info(self, mock_response):
        """Testa obtenção de informações sobre transação"""
        txid = "0000000000000000000000000000000000000000000000000000000000000001"
        network = "testnet"
        
        # Mock para a API Blockstream
        mock_response.json.return_value = {
            "txid": txid,
            "version": 1,
            "locktime": 0,
            "size": 250,
            "weight": 1000,
            "fee": 500,
            "status": {
                "confirmed": True,
                "block_height": 1000,
                "block_hash": "0000000000000000000000000000000000000000000000000000000000000002",
                "block_time": 1600000000
            }
        }
        
        with patch("app.services.blockchain_service.requests.get") as mock_get:
            mock_get.return_value = mock_response
            
            result = get_transaction_info(txid, network)
            
            # Verificar chamada à API
            mock_get.assert_called_once()
            assert f"testnet/api/tx/{txid}" in mock_get.call_args[0][0]
            
            # Verificar dados da transação
            assert result["txid"] == txid
            assert result["confirmations"] > 0
            assert result["confirmed"] is True
            assert "block_height" in result
            assert "block_hash" in result
            assert result["block_height"] == 1000
    
    def test_save_and_load_cache(self, cache_dir):
        """Testa salvamento e carregamento de cache"""
        # Dados para cache
        cache_data = {
            "test_key": {"value": "test_value"}
        }
        
        # Caminho do arquivo de cache
        cache_file = os.path.join(cache_dir, "blockchain_cache.json")
        
        # Testar salvamento
        save_to_cache(cache_data, cache_dir)
        
        # Verificar se o arquivo foi criado
        assert os.path.exists(cache_file)
        
        # Testar carregamento
        loaded_data = load_from_cache(cache_dir)
        
        # Verificar dados carregados
        assert "test_key" in loaded_data
        assert loaded_data["test_key"]["value"] == "test_value"
    
    def test_check_connection(self):
        """Testa verificação de conexão com a API blockchain"""
        network = "testnet"
        
        with patch("app.services.blockchain_service.requests.get") as mock_get:
            # Caso de sucesso
            mock_get.return_value = MagicMock(status_code=200)
            
            result = check_connection(network)
            assert result is True
            
            # Caso de falha por exceção
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            result = check_connection(network)
            assert result is False
            
            # Caso de falha por código de status
            mock_get.side_effect = None
            mock_get.return_value = MagicMock(status_code=404)
            
            result = check_connection(network)
            assert result is False 