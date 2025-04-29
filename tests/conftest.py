import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import tempfile

sys.path.append(str(Path(__file__).parent.parent))

from app.models.utxo_models import Input, Output, TransactionRequest

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

@pytest.fixture
def test_address_testnet():
    """Fornece um endereço Bitcoin de teste na testnet"""
    return "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"

@pytest.fixture
def test_address_mainnet():
    """Fornece um endereço Bitcoin de teste na mainnet"""
    return "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

@pytest.fixture
def test_private_key_testnet():
    """Fornece uma chave privada de teste para a rede de testes"""
    return "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"

@pytest.fixture
def test_public_key():
    """Fornece uma chave pública de teste"""
    return "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"

@pytest.fixture
def test_transaction_data():
    """Fornece dados de transação de exemplo"""
    return {
        "raw_transaction": "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000",
        "txid": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
        "fee": 10000
    }

@pytest.fixture
def test_utxos():
    """Fornece UTXOs de exemplo"""
    return [
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
            "confirmations": 2,
            "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac"
        }
    ]

@pytest.fixture
def test_balance_data():
    """Fornece dados de saldo de exemplo"""
    return {
        "confirmed": 5000000,
        "unconfirmed": 1000000,
        "total": 6000000
    }

@pytest.fixture
def sample_tx_request():
    """Fornece uma requisição de transação de exemplo"""
    return TransactionRequest(
        inputs=[
            Input(
                txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                vout=0,
                value=5000000,
                script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
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