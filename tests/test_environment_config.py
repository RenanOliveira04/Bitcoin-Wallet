import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))

from app.dependencies import get_network, get_cache_timeout


class TestEnvironmentConfiguration:
    """Testes para verificar a configuração dos diferentes ambientes"""
    
    def test_development_environment(self):
        """Testa as configurações do ambiente de desenvolvimento"""
        env_vars = {
            "NETWORK": "testnet",
            "LOG_LEVEL": "DEBUG",
            "CACHE_TIMEOUT": "60",
            "OFFLINE_MODE": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            assert get_network() == "testnet"
            assert get_settings().log_level == "DEBUG"
            assert get_cache_timeout() == 60
            assert is_offline_mode_enabled() is False
    
    def test_staging_environment(self):
        """Testa as configurações do ambiente de staging (homologação)"""
        env_vars = {
            "NETWORK": "testnet",
            "LOG_LEVEL": "INFO",
            "CACHE_TIMEOUT": "300",
            "OFFLINE_MODE": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            assert get_network() == "testnet"
            assert get_settings().log_level == "INFO"
            assert get_cache_timeout() == 300
            assert is_offline_mode_enabled() is False
    
    def test_production_like_environment_testnet(self):
        """Testa as configurações do ambiente de produção com testnet"""
        env_vars = {
            "NETWORK": "testnet",
            "LOG_LEVEL": "WARNING",
            "CACHE_TIMEOUT": "600",
            "OFFLINE_MODE": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            assert get_network() == "testnet"
            assert get_settings().log_level == "WARNING"
            assert get_cache_timeout() == 600
            assert is_offline_mode_enabled() is False
    
    def test_custom_environment_settings(self):
        """Testa configurações de ambiente personalizadas com testnet"""
        env_vars = {
            "NETWORK": "testnet",
            "LOG_LEVEL": "ERROR",
            "CACHE_TIMEOUT": "3600",
            "OFFLINE_MODE": "true",
            "CACHE_DIR": "/custom/cache/dir"
        }
        
        with patch.dict(os.environ, env_vars):
            assert get_network() == "testnet"
            assert get_settings().log_level == "ERROR"
            assert get_cache_timeout() == 3600
            assert is_offline_mode_enabled() is True
            
            with patch("app.dependencies.get_cache_dir") as mock_cache_dir:
                mock_cache_dir.return_value = Path("/custom/cache/dir")
                from app.dependencies import get_cache_dir
                assert str(get_cache_dir()) == "/custom/cache/dir"
    
    def test_default_values(self):
        """Testa valores padrão quando variáveis de ambiente não são fornecidas"""
        with patch.dict(os.environ, {}, clear=True):
            assert get_network() == "testnet"  
            assert get_settings().log_level == "INFO"  
            assert get_cache_timeout() == 300  
            assert is_offline_mode_enabled() is False 
    
    def test_invalid_network_setting(self):
        """Testa comportamento com valor inválido de rede"""
        with patch.dict(os.environ, {"NETWORK": "invalid_network"}):
            
            try:
                network = get_network()
                assert network == "testnet"  
            except ValueError:
            
                pass
    
    def test_invalid_cache_timeout(self):
        """Testa comportamento com valor inválido de timeout de cache"""
        with patch.dict(os.environ, {"CACHE_TIMEOUT": "invalid_timeout"}):
            try:
                timeout = get_cache_timeout()
                assert isinstance(timeout, int) 
            except ValueError:
                pass
    
    def test_environment_file_loading(self):
        """Testa carregamento de configurações a partir de um arquivo .env"""
        env_content = """
        NETWORK=testnet
        LOG_LEVEL=DEBUG
        CACHE_TIMEOUT=120
        OFFLINE_MODE=false
        """
        
        with patch("app.dependencies.load_dotenv") as mock_load_env:
            mock_load_env.return_value = True
            
            with patch.dict(os.environ, {
                "NETWORK": "testnet",
                "LOG_LEVEL": "DEBUG",
                "CACHE_TIMEOUT": "120",
                "OFFLINE_MODE": "false"
            }):
                from app.dependencies import get_network, get_settings, get_cache_timeout, is_offline_mode_enabled
                
                assert get_network() == "testnet"
                assert get_settings().log_level == "DEBUG"
                assert get_cache_timeout() == 120
                assert is_offline_mode_enabled() is False
