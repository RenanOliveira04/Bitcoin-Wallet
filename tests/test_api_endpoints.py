import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.models.balance_models import BalanceResponse
from app.models.utxo_models import UTXOResponse, TransactionRequest, TransactionResponse
from app.models.wallet_models import WalletResponse, WalletCreate


class TestAPIEndpoints:
    """Testes para os endpoints da API"""
    
    @pytest.fixture
    def client(self):
        """Fixture para criar um cliente de teste para a FastAPI"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_address(self):
        """Fixture para um endereço de teste"""
        return "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
    
    @pytest.fixture
    def sample_balance_response(self):
        """Fixture para uma resposta de saldo"""
        return {
            "confirmed": 5000000,
            "unconfirmed": 1000000,
            "total": 6000000
        }
    
    @pytest.fixture
    def sample_utxo_response(self):
        """Fixture para uma resposta de UTXOs"""
        return [
            {
                "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                "vout": 0,
                "value": 5000000,
                "confirmations": 6,
                "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac"
            }
        ]
    
    @pytest.fixture
    def sample_tx_request(self):
        """Fixture para uma requisição de transação"""
        return {
            "inputs": [
                {
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "vout": 0,
                    "value": 5000000,
                    "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    "address": "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
                }
            ],
            "outputs": [
                {
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    "value": 4990000
                }
            ],
            "fee_rate": 2.0
        }
    
    @pytest.fixture
    def sample_tx_response(self):
        """Fixture para uma resposta de transação"""
        return {
            "transaction_hex": "020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff",
            "txid": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
            "fee": 10000
        }
    
    @pytest.fixture
    def sample_wallet_create(self):
        """Fixture para dados de criação de carteira"""
        return {
            "address": "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc",
            "public_key": "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
            "private_key_encrypted": "encrypted_key_data",
            "format": "p2pkh",
            "network": "testnet",
            "name": "Test Wallet"
        }
    
    def test_health_endpoint(self, client):
        """Testa o endpoint de health check"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_metrics_endpoint(self, client):
        """Testa o endpoint de métricas"""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        assert "uptime" in response.json()
    
    def test_get_balance_endpoint(self, client, sample_address, sample_balance_response):
        """Testa o endpoint de obtenção de saldo"""
        with patch("app.routers.balance.get_balance") as mock_get_balance:
            mock_get_balance.return_value = sample_balance_response
            
            response = client.get(f"/api/balance/{sample_address}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["confirmed"] == 5000000
            assert data["unconfirmed"] == 1000000
            assert data["total"] == 6000000
            
            mock_get_balance.assert_called_once()
    
    def test_get_balance_with_invalid_address(self, client):
        """Testa o endpoint de obtenção de saldo com endereço inválido"""
        response = client.get("/api/balance/invalid_address")
        
        assert response.status_code == 422  
    
    def test_get_utxos_endpoint(self, client, sample_address, sample_utxo_response):
        """Testa o endpoint de obtenção de UTXOs"""
        with patch("app.routers.balance.get_utxos") as mock_get_utxos:
            mock_get_utxos.return_value = sample_utxo_response
            
            response = client.get(f"/api/utxos/{sample_address}")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["txid"] == "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
            assert data[0]["value"] == 5000000
            
            mock_get_utxos.assert_called_once()
    
    def test_build_transaction_endpoint_bitcoinlib(self, client, sample_tx_request, sample_tx_response):
        """Testa o endpoint de construção de transação usando BitcoinLibBuilder"""
        with patch("app.routers.tx.BitcoinLibBuilder.build") as mock_build:
            mock_build.return_value = TransactionResponse(**sample_tx_response)
            
            response = client.post("/api/tx/build", json=sample_tx_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["txid"] == sample_tx_response["txid"]
            assert data["transaction_hex"] == sample_tx_response["transaction_hex"]
            assert data["fee"] == sample_tx_response["fee"]
            
            mock_build.assert_called_once()
    
    def test_build_transaction_endpoint_bitcoin_core(self, client, sample_tx_request, sample_tx_response):
        """Testa o endpoint de construção de transação usando BitcoinCoreBuilder"""
        with patch("app.routers.tx.BitcoinCoreBuilder.build") as mock_build:
            mock_build.return_value = TransactionResponse(**sample_tx_response)
            
            response = client.post("/api/tx/build?builder_type=bitcoincore", json=sample_tx_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["txid"] == sample_tx_response["txid"]
            
            mock_build.assert_called_once()
    
    def test_broadcast_transaction_endpoint(self, client):
        """Testa o endpoint de broadcast de transação"""
        tx_hex = "020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff"
        
        with patch("app.routers.tx.broadcast_transaction") as mock_broadcast:
            mock_broadcast.return_value = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            
            response = client.post("/api/tx/broadcast", json={"transaction_hex": tx_hex})
            
            assert response.status_code == 200
            data = response.json()
            assert "txid" in data
            assert data["txid"] == "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            
            mock_broadcast.assert_called_once_with(tx_hex, "testnet")  # Assumindo testnet como padrão
    
    def test_get_transaction_status_endpoint(self, client):
        """Testa o endpoint de status de transação"""
        txid = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
        
        with patch("app.routers.tx.get_transaction_status") as mock_status:
            mock_status.return_value = {
                "confirmed": True,
                "block_height": 700000,
                "confirmations": 5,
                "timestamp": 1635000000
            }
            
            response = client.get(f"/api/tx/{txid}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["confirmed"] is True
            assert data["confirmations"] == 5
            
            mock_status.assert_called_once()
    
    def test_wallets_crud_endpoints(self, client, sample_wallet_create):
        """Testa os endpoints CRUD para carteiras"""
        with patch("app.routers.wallets.wallet_storage") as mock_storage:
            mock_storage.get_all_wallets.return_value = [
                WalletResponse(**sample_wallet_create, id=1)
            ]
            
            response = client.get("/api/wallets")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["address"] == sample_wallet_create["address"]
            
            mock_storage.create_wallet.return_value = WalletResponse(**sample_wallet_create, id=1)
            
            response = client.post("/api/wallets", json=sample_wallet_create)
            assert response.status_code == 200
            data = response.json()
            assert data["address"] == sample_wallet_create["address"]
            assert data["name"] == sample_wallet_create["name"]
            
            mock_storage.get_wallet.return_value = WalletResponse(**sample_wallet_create, id=1)
            
            response = client.get(f"/api/wallets/{sample_wallet_create['address']}")
            assert response.status_code == 200
            data = response.json()
            assert data["address"] == sample_wallet_create["address"]
            
            mock_storage.delete_wallet.return_value = True
            
            response = client.delete(f"/api/wallets/{sample_wallet_create['address']}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_wallet_transactions_endpoints(self, client, sample_address):
        """Testa os endpoints de transações de carteira"""
        with patch("app.routers.wallets.wallet_storage") as mock_storage:
            mock_storage.get_wallet_transactions.return_value = [
                {
                    "txid": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
                    "wallet_address": sample_address,
                    "amount": 5000000,
                    "fee": 1000,
                    "confirmations": 5,
                    "timestamp": 1635000000,
                    "type": "receive"
                }
            ]
            
            response = client.get(f"/api/wallets/{sample_address}/transactions")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["txid"] == "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
    
    def test_wallet_utxos_endpoints(self, client, sample_address):
        """Testa os endpoints de UTXOs de carteira"""
        with patch("app.routers.wallets.wallet_storage") as mock_storage:
            mock_storage.get_wallet_utxos.return_value = [
                {
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "vout": 0,
                    "amount": 5000000,
                    "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    "wallet_address": sample_address,
                    "confirmations": 6
                }
            ]
            
            response = client.get(f"/api/wallets/{sample_address}/utxos")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["txid"] == "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e"
    
    def test_key_generation_endpoints(self, client):
        """Testa os endpoints de geração de chaves"""
        with patch("app.routers.keys.generate_key_pair") as mock_gen_key:
            mock_gen_key.return_value = (
                "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi",
                "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            )
            
            response = client.get("/api/keys/generate?network=testnet")
            assert response.status_code == 200
            data = response.json()
            assert "private_key" in data
            assert "public_key" in data
            
            mock_gen_key.assert_called_once()
        
        with patch("app.routers.keys.derive_address") as mock_derive_addr:
            mock_derive_addr.return_value = "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
            
            public_key = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
            response = client.get(f"/api/keys/address?public_key={public_key}&address_type=p2pkh&network=testnet")
            assert response.status_code == 200
            data = response.json()
            assert "address" in data
            
            mock_derive_addr.assert_called_once()
