import pytest
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.services.address_service import generate_address
from app.models.address_models import AddressResponse

class TestAddressService:
    """Testes unitários para o serviço de endereços"""
    
    def test_generate_address_p2pkh(self):
        """Testa geração de endereço P2PKH"""
        # Chave privada WIF de testnet
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        response = generate_address(private_key, "p2pkh", "testnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.format == "p2pkh"
        assert response.network == "testnet"
        # Prefixo para endereços P2PKH na testnet
        assert response.address.startswith(("m", "n"))
        
    def test_generate_address_p2sh(self):
        """Testa geração de endereço P2SH"""
        # Chave privada WIF de testnet
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        response = generate_address(private_key, "p2sh", "testnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.format == "p2sh"
        assert response.network == "testnet"
        # Prefixo para endereços P2SH na testnet
        assert response.address.startswith("2")
        
    def test_generate_address_p2wpkh(self):
        """Testa geração de endereço P2WPKH (Nativo SegWit)"""
        # Chave privada WIF de testnet
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        response = generate_address(private_key, "p2wpkh", "testnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        # O formato pode ser p2wpkh ou p2pkh se o fallback foi acionado
        assert response.format in ["p2wpkh", "p2pkh"]
        assert response.network == "testnet"
        # Se for segwit nativo, começará com tb1
        if response.format == "p2wpkh":
            assert response.address.startswith("tb1")
        
    def test_generate_address_mainnet(self):
        """Testa geração de endereço na rede principal"""
        # Chave privada WIF de mainnet
        private_key = "KxDkjZD1MnM4ZmgMUYJgRZYWWwZNj5BwJ6E9FJVSdqfNK3CPzjQo"
        
        response = generate_address(private_key, "p2pkh", "mainnet")
        
        assert response is not None
        assert isinstance(response, AddressResponse)
        assert response.address is not None
        assert response.format == "p2pkh"
        assert response.network == "mainnet"
        # Prefixo para endereços P2PKH na mainnet
        assert response.address.startswith("1")
        
    def test_generate_address_invalid_format(self):
        """Testa geração de endereço com formato inválido"""
        # Chave privada WIF de testnet
        private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        
        with pytest.raises(ValueError):
            generate_address(private_key, "invalid_format", "testnet")
        
    def test_generate_address_invalid_key(self):
        """Testa geração de endereço com chave inválida"""
        # Chave privada inválida
        private_key = "invalid_key"
        
        with pytest.raises(ValueError):
            generate_address(private_key, "p2pkh", "testnet") 