import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import tempfile

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

@pytest.fixture
def mock_response():
    """Fixture para criar um mock de resposta HTTP"""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {}
    return mock

@pytest.fixture
def temp_keys_dir():
    """Fixture para criar um diretório temporário para chaves"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def temp_cache_dir():
    """Fixture para criar um diretório temporário para cache"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        cache_dir = os.path.join(tmpdirname, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        yield cache_dir

@pytest.fixture
def test_address_testnet():
    """Fixture para fornecer um endereço de teste na testnet"""
    return "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"

@pytest.fixture
def test_address_mainnet():
    """Fixture para fornecer um endereço de teste na mainnet"""
    return "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"

@pytest.fixture
def test_private_key_testnet():
    """Fixture para fornecer uma chave privada de teste para testnet"""
    return "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"

@pytest.fixture
def test_public_key():
    """Fixture para fornecer uma chave pública de teste"""
    return "02e2fcd9d80f35af180926bd94c81e3e79c3c2fd37d79ce4609f1bb36993f461e9"

@pytest.fixture
def test_transaction_data():
    """Fixture para fornecer dados de transação de teste"""
    return {
        "txid": "0000000000000000000000000000000000000000000000000000000000000001",
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

@pytest.fixture
def test_utxos():
    """Fixture para fornecer UTXOs de teste"""
    return [
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

@pytest.fixture
def test_balance_data():
    """Fixture para fornecer dados de saldo de teste"""
    return {
        "chain_stats": {"funded_txo_sum": 1000000, "spent_txo_sum": 500000},
        "mempool_stats": {"funded_txo_sum": 200000, "spent_txo_sum": 0}
    } 