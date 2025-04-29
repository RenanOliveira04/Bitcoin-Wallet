import pytest
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.services.address_service import (
    validate_address, 
    generate_multisig, 
    parse_script
)

class TestAddressService:
    """Testes unitários para o serviço de endereços"""
    
    def test_validate_address_valid_p2pkh_testnet(self):
        """Testa validação de endereço P2PKH válido na testnet"""
        address = "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn"
        result = validate_address(address, "testnet")
        
        assert result is True
        
    def test_validate_address_valid_p2sh_testnet(self):
        """Testa validação de endereço P2SH válido na testnet"""
        address = "2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc"
        result = validate_address(address, "testnet")
        
        assert result is True
        
    def test_validate_address_valid_bech32_testnet(self):
        """Testa validação de endereço Bech32 válido na testnet"""
        address = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
        result = validate_address(address, "testnet")
        
        assert result is True
        
    def test_validate_address_valid_p2pkh_mainnet(self):
        """Testa validação de endereço P2PKH válido na mainnet"""
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        result = validate_address(address, "mainnet")
        
        assert result is True
        
    def test_validate_address_valid_p2sh_mainnet(self):
        """Testa validação de endereço P2SH válido na mainnet"""
        address = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
        result = validate_address(address, "mainnet")
        
        assert result is True
        
    def test_validate_address_valid_bech32_mainnet(self):
        """Testa validação de endereço Bech32 válido na mainnet"""
        address = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        result = validate_address(address, "mainnet")
        
        assert result is True
        
    def test_validate_address_invalid(self):
        """Testa validação de endereço inválido"""
        address = "invalid_bitcoin_address"
        result = validate_address(address, "testnet")
        
        assert result is False
        
    def test_validate_address_wrong_network(self):
        """Testa validação de endereço na rede incorreta"""
        # Endereço mainnet sendo validado na testnet
        address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        result = validate_address(address, "testnet")
        
        assert result is False
        
        # Endereço testnet sendo validado na mainnet
        address = "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn"
        result = validate_address(address, "mainnet")
        
        assert result is False
        
    def test_generate_multisig(self):
        """Testa geração de endereço multisig"""
        public_keys = [
            "03a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c7",
            "03774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb",
            "03d01115d548e7561b15c38f004d734633687cf4419620095bc5b0f47070afe85a"
        ]
        
        # Endereço multisig 2-de-3
        result = generate_multisig(public_keys, 2, "testnet")
        
        assert result is not None
        assert "address" in result
        assert "redeem_script" in result
        assert result["address"].startswith("2")  # P2SH na testnet
        assert len(result["redeem_script"]) > 0
        
    def test_generate_multisig_p2wsh(self):
        """Testa geração de endereço multisig P2WSH"""
        public_keys = [
            "03a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c7",
            "03774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb",
            "03d01115d548e7561b15c38f004d734633687cf4419620095bc5b0f47070afe85a"
        ]
        
        # Endereço multisig 2-de-3 no formato P2WSH
        result = generate_multisig(public_keys, 2, "testnet", address_type="p2wsh")
        
        assert result is not None
        assert "address" in result
        assert "redeem_script" in result
        assert result["address"].startswith("tb1")  # Bech32 na testnet
        assert len(result["redeem_script"]) > 0
        
    def test_parse_script(self):
        """Testa análise de script de resgate"""
        # Script de resgate de um multisig 2-de-3
        script = "522103a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c72103774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb2103d01115d548e7561b15c38f004d734633687cf4419620095bc5b0f47070afe85a53ae"
        
        result = parse_script(script)
        
        assert result is not None
        assert "type" in result
        assert "required_signatures" in result
        assert "public_keys" in result
        assert result["type"] == "multisig"
        assert result["required_signatures"] == 2
        assert len(result["public_keys"]) == 3 