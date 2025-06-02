import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json

sys.path.append(str(Path(__file__).parent.parent))

from app.services.blockchain_service import get_balance, get_utxos, PersistentBlockchainCache
from app.services.transaction import BitcoinLibBuilder, BitcoinCoreBuilder
from app.models.utxo_models import Input, Output, TransactionRequest
from app.dependencies import get_network, get_cache_dir, is_offline_mode_enabled


class TestColdWalletFunctionality:
    """Testes abrangentes para as funcionalidades de cold wallet"""
    
    @pytest.fixture
    def mock_cache_dir(self, temp_cache_dir):
        """Fixture para simular o diretório de cache"""
        with patch('app.services.blockchain_service.get_cache_dir') as mock_dir:
            mock_dir.return_value = Path(temp_cache_dir)
            yield temp_cache_dir

    @pytest.fixture
    def populated_cache(self, mock_cache_dir):
        """Fixture para criar um cache pré-populado para testes offline"""
        cache = PersistentBlockchainCache()
        
        balance_data = {
            "confirmed": 5000000,
            "unconfirmed": 1000000,
            "total": 6000000
        }
        
        utxo_data = [
            {
                "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                "vout": 0,
                "value": 5000000,
                "confirmations": 6,
                "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac"
            },
            {
                "txid": "8b1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283f",
                "vout": 1,
                "value": 1000000,
                "confirmations": 0,
                "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac"
            }
        ]
        
        address = "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
        network = "testnet"
        
        cache.set(f"balance_{network}_{address}", balance_data)
        cache.set(f"utxos_{network}_{address}", utxo_data)
        
        return {"address": address, "network": network}
    
    def test_offline_mode_environment_variable(self):
        """Testa se a variável de ambiente OFFLINE_MODE é corretamente interpretada"""
        with patch.dict(os.environ, {"OFFLINE_MODE": "true"}):
            assert get_offline_mode() is True
        
        with patch.dict(os.environ, {"OFFLINE_MODE": "false"}):
            assert get_offline_mode() is False
        
        with patch.dict(os.environ, {"OFFLINE_MODE": ""}):
            assert get_offline_mode() is False
    
    def test_cache_dir_environment_variable(self):
        """Testa se a variável de ambiente CACHE_DIR é corretamente interpretada"""
        test_dir = "/test/cache/dir"
        with patch.dict(os.environ, {"CACHE_DIR": test_dir}):
            assert str(get_cache_dir()) == test_dir
    
    def test_offline_balance_retrieval(self, populated_cache):
        """Testa a obtenção de saldo no modo offline"""
        address = populated_cache["address"]
        network = populated_cache["network"]
        
        with patch('app.services.blockchain_service.requests.get') as mock_get:
            result = get_balance(address, network, offline_mode=True)
            
            mock_get.assert_not_called()
            
            assert result["confirmed"] == 5000000
            assert result["unconfirmed"] == 1000000
            assert result["total"] == 6000000
    
    def test_offline_utxos_retrieval(self, populated_cache):
        """Testa a obtenção de UTXOs no modo offline"""
        address = populated_cache["address"]
        network = populated_cache["network"]
        
        with patch('app.services.blockchain_service.requests.get') as mock_get:
            result = get_utxos(address, network, offline_mode=True)
            
            mock_get.assert_not_called()
            
            assert len(result) == 2
            assert result[0]["txid"] == "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
            assert result[0]["value"] == 5000000
            assert result[1]["txid"] == "8b1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283f"
            assert result[1]["value"] == 1000000
    
    def test_offline_transaction_building(self, populated_cache):
        """Testa a construção de transações no modo offline"""
        address = populated_cache["address"]
        
        tx_request = TransactionRequest(
            inputs=[
                Input(
                    txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    vout=0,
                    value=5000000,
                    script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    address=address
                )
            ],
            outputs=[
                Output(
                    address="tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    value=4990000
                )
            ],
            fee_rate=2.0
        )
        
        lib_builder = BitcoinLibBuilder()
        with patch('app.services.transaction.builders.bitcoin_lib_builder.Input'), \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Output'), \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Transaction') as mock_tx:
            
            mock_tx_instance = MagicMock()
            mock_tx_instance.hash = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.sign = MagicMock()
            mock_tx_instance.raw_hex = MagicMock(return_value="020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff")
            mock_tx.return_value = mock_tx_instance
            
            result = lib_builder.build(tx_request, network="testnet")
            
            assert result is not None
            assert "transaction_hex" in result.dict()
            assert "txid" in result.dict()
    
    def test_cache_timeout_configuration(self):
        """Testa a configuração de timeout do cache"""
        with patch.dict(os.environ, {"CACHE_TIMEOUT": "3600"}):
            with patch('app.services.blockchain_service.get_cache_timeout') as mock_get_timeout, \
                 patch('app.services.blockchain_service.get_cache_dir'), \
                 patch('builtins.open', mock_open()), \
                 patch('json.dump'):
                
                mock_get_timeout.return_value = 3600
                
                cache = PersistentBlockchainCache()
                assert cache.timeout == 3600
    
    def test_cache_persistence(self, mock_cache_dir):
        """Testa a persistência do cache em disco"""
        cache = PersistentBlockchainCache()
        
        test_key = "test_key"
        test_value = {"value": "test_value"}
        
        cache.set(test_key, test_value)
        
        cache2 = PersistentBlockchainCache()
        
        assert cache2.get(test_key) == test_value
        
        cache_file = Path(mock_cache_dir) / "blockchain_cache.json"
        assert cache_file.exists()
    
    def test_cache_expiration(self, mock_cache_dir):
        """Testa a expiração de itens no cache"""
        with patch('app.services.blockchain_service.get_cache_timeout') as mock_get_timeout:
            mock_get_timeout.return_value = 0 
            
            cache = PersistentBlockchainCache()
            
            test_key = "test_key"
            test_value = {"value": "test_value"}
            
            cache.set(test_key, test_value)
            
            assert cache.get(test_key) is None
