import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.routers.health import NETWORK_TEST_ADDRESSES

client = TestClient(app)

class TestHealthRouter:
    """Testes unitários para o router de health check"""
    
    def test_health_endpoint_success(self):
        """Testa o endpoint /health quando todas as redes estão operacionais"""
        with patch('app.routers.health.get_balance') as mock_get_balance:
            # Configurar o mock para retornar um valor válido
            mock_get_balance.return_value = {"confirmed": 1000, "unconfirmed": 0}
            
            # Fazer a requisição ao endpoint
            response = client.get("/api/health")
            
            # Verificar status code
            assert response.status_code == 200
            
            # Verificar estrutura da resposta
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            assert "networks" in data
            
            # Verificar se as redes estão presentes e operacionais
            assert "mainnet" in data["networks"]
            assert "testnet" in data["networks"]
            assert data["networks"]["mainnet"]["status"] == "ok"
            assert data["networks"]["testnet"]["status"] == "ok"
            
            # Verificar se o mock foi chamado corretamente
            assert mock_get_balance.call_count == 2
            mock_get_balance.assert_any_call(
                NETWORK_TEST_ADDRESSES["mainnet"], 
                "mainnet", 
                offline_mode=False
            )
            mock_get_balance.assert_any_call(
                NETWORK_TEST_ADDRESSES["testnet"], 
                "testnet", 
                offline_mode=False
            )
    
    def test_health_endpoint_degraded(self):
        """Testa o endpoint /health quando uma rede está com problemas"""
        with patch('app.routers.health.get_balance') as mock_get_balance:
            # Configurar o mock para retornar um valor válido para mainnet
            # e levantar exceção para testnet
            def mock_get_balance_side_effect(address, network, offline_mode):
                if network == "mainnet":
                    return {"confirmed": 1000, "unconfirmed": 0}
                else:
                    raise Exception("Erro de conexão com a rede testnet")
            
            mock_get_balance.side_effect = mock_get_balance_side_effect
            
            # Fazer a requisição ao endpoint
            response = client.get("/api/health")
            
            # Verificar status code
            assert response.status_code == 200
            
            # Verificar estrutura da resposta
            data = response.json()
            assert "status" in data
            assert data["status"] == "degraded"
            assert "networks" in data
            
            # Verificar se as redes estão presentes com status corretos
            assert data["networks"]["mainnet"]["status"] == "ok"
            assert data["networks"]["testnet"]["status"] == "error"
            assert "error" in data["networks"]["testnet"]
            assert "connection" in data["networks"]["testnet"]
            assert data["networks"]["testnet"]["connection"] == "offline"
    
    def test_health_endpoint_unhealthy(self):
        """Testa o endpoint /health quando ocorre um erro crítico"""
        with patch('app.routers.health.get_balance') as mock_get_balance:
            # Configurar o mock para levantar uma exceção crítica
            mock_get_balance.side_effect = Exception("Erro crítico do sistema")
            
            # Fazer a requisição ao endpoint
            response = client.get("/api/health")
            
            # Verificar status code
            assert response.status_code == 200
            
            # Verificar estrutura da resposta
            data = response.json()
            assert "status" in data
            assert data["status"] == "unhealthy"
            assert "error" in data
            
    def test_metrics_endpoint_success(self):
        """Testa o endpoint /metrics quando todas as redes estão operacionais"""
        with patch('app.routers.health.get_balance') as mock_get_balance:
            # Configurar o mock para retornar valores válidos
            mock_get_balance.return_value = {"confirmed": 1000, "unconfirmed": 50}
            
            # Fazer a requisição ao endpoint
            response = client.get("/api/metrics")
            
            # Verificar status code
            assert response.status_code == 200
            
            # Verificar estrutura da resposta
            data = response.json()
            assert "mainnet" in data
            assert "testnet" in data
            
            # Verificar os valores das métricas
            assert data["mainnet"]["confirmed_balance"] == 1000
            assert data["mainnet"]["unconfirmed_balance"] == 50
            assert data["testnet"]["confirmed_balance"] == 1000
            assert data["testnet"]["unconfirmed_balance"] == 50
            
            # Verificar se o mock foi chamado corretamente
            assert mock_get_balance.call_count == 2
    
    def test_metrics_endpoint_partial_failure(self):
        """Testa o endpoint /metrics quando uma rede está com problemas"""
        with patch('app.routers.health.get_balance') as mock_get_balance:
            # Configurar o mock para retornar um valor válido para mainnet
            # e levantar exceção para testnet
            def mock_get_balance_side_effect(address, network, offline_mode):
                if network == "mainnet":
                    return {"confirmed": 1000, "unconfirmed": 50}
                else:
                    raise Exception("Erro de conexão com a rede testnet")
            
            mock_get_balance.side_effect = mock_get_balance_side_effect
            
            # Fazer a requisição ao endpoint
            response = client.get("/api/metrics")
            
            # Verificar status code
            assert response.status_code == 200
            
            # Verificar estrutura da resposta
            data = response.json()
            assert "mainnet" in data
            assert "testnet" in data
            
            # Verificar que mainnet tem dados válidos
            assert data["mainnet"]["confirmed_balance"] == 1000
            assert data["mainnet"]["unconfirmed_balance"] == 50
            
            # Verificar que testnet tem erro e valores padrão
            assert "error" in data["testnet"]
            assert data["testnet"]["confirmed_balance"] == 0
            assert data["testnet"]["unconfirmed_balance"] == 0
    
    def test_metrics_endpoint_full_failure(self):
        """Testa o endpoint /metrics quando ocorre um erro crítico"""
        with patch('app.routers.health.get_balance') as mock_get_balance:
            # Configurar o mock para levantar uma exceção crítica
            mock_get_balance.side_effect = Exception("Erro crítico do sistema")
            
            # Fazer a requisição ao endpoint
            response = client.get("/api/metrics")
            
            # Verificar status code
            assert response.status_code == 200
            
            # Verificar estrutura da resposta
            data = response.json()
            assert "error" in data
            assert "mainnet" in data
            assert "testnet" in data
            
            # Verificar que ambas as redes têm valores padrão zero
            assert data["mainnet"]["confirmed_balance"] == 0
            assert data["mainnet"]["unconfirmed_balance"] == 0
            assert data["testnet"]["confirmed_balance"] == 0
            assert data["testnet"]["unconfirmed_balance"] == 0 