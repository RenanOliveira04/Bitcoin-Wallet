import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.services.address_service import generate_address
from app.models.address_models import AddressResponse

class TestAddressService:
    """Testes unitários para o serviço de endereços"""
    
    @patch('app.services.address_service.Key')
    def test_generate_address_p2pkh(self, mock_key):
        """Testa geração de endereço P2PKH"""
        mock_key_instance = MagicMock()
        mock_key_instance.address.return_value = "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
        mock_key.return_value = mock_key_instance
        
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        response = generate_address(private_key, "p2pkh", "testnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.address == "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
        assert response.format == "p2pkh"
        assert response.network == "testnet"
        
    @patch('app.services.address_service.Key')
    def test_generate_address_p2sh(self, mock_key):
        """Testa geração de endereço P2SH"""
        mock_key_instance = MagicMock()
        mock_key_instance.address_p2sh.return_value = "2N8hwP1WmJrFF5QWABn38y63uYLhnJYJYTF"
        mock_key.return_value = mock_key_instance
        
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        response = generate_address(private_key, "p2sh", "testnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.address == "2N8hwP1WmJrFF5QWABn38y63uYLhnJYJYTF"
        assert response.format == "p2sh"
        assert response.network == "testnet"
        
    @patch('app.services.address_service.Key')
    def test_generate_address_p2wpkh(self, mock_key):
        """Testa geração de endereço P2WPKH (Nativo SegWit)"""
        mock_key_instance = MagicMock()
        mock_key_instance.address_segwit = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        mock_key.return_value = mock_key_instance
        
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        response = generate_address(private_key, "p2wpkh", "testnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.address == "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        assert response.format == "p2wpkh"
        assert response.network == "testnet"
        
    @patch('app.services.address_service.Key')
    def test_generate_address_mainnet(self, mock_key):
        """Testa geração de endereço na rede principal"""
        mock_key_instance = MagicMock()
        mock_key_instance.address.return_value = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        mock_key.return_value = mock_key_instance
        
        private_key = "KxDkjZD1MnM4ZmgMUYJgRZYWWwZNj5BwJ6E9FJVSdqfNK3CPzjQo"
        
        response = generate_address(private_key, "p2pkh", "mainnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.address == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        assert response.format == "p2pkh"
        assert response.network == "mainnet"
        
    @patch('app.services.address_service.Key')
    def test_generate_address_invalid_format(self, mock_key):
        """Testa geração de endereço com formato inválido"""
        mock_key_instance = MagicMock()
        mock_key.return_value = mock_key_instance
        
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        with pytest.raises(ValueError):
            generate_address(private_key, "invalid_format", "testnet")
        
    @patch('app.services.address_service.Key')
    @patch('app.services.address_service.HDKey.from_wif')
    @patch('app.services.address_service.HDKey')
    def test_generate_address_invalid_key(self, mock_hdkey, mock_hdkey_from_wif, mock_key):
        """Testa geração de endereço com chave inválida"""
        mock_key.side_effect = ValueError("Invalid key")
        mock_hdkey_from_wif.side_effect = ValueError("Invalid key")
        mock_hdkey.side_effect = ValueError("Invalid key")
        
        private_key = "invalid_key"
        
        with pytest.raises(ValueError) as excinfo:
            generate_address(private_key, "p2pkh", "testnet")
            
        assert "Não foi possível carregar a chave privada" in str(excinfo.value) 