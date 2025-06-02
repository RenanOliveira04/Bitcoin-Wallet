import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.services.key_service import generate_key
from app.models.key_models import KeyRequest


class TestKeyGeneration:
    """Testes para geração de diferentes tipos de chaves Bitcoin"""
    
    def test_p2pkh_key_generation(self):
        """Testa a geração de chaves para endereços P2PKH"""
        request = KeyRequest(
            method="entropy",
            key_type="p2pkh",
            network="testnet"
        )
        result = generate_key(request)
        
        assert result.private_key is not None
        assert result.public_key is not None
        assert result.address.startswith(('m', 'n'))  
    
    def test_p2sh_key_generation(self):
        """Testa a geração de chaves para endereços P2SH"""
        request = KeyRequest(
            method="entropy",
            key_type="p2sh",
            network="testnet"
        )
        result = generate_key(request)
        
        assert result.address is not None
        assert result.address.startswith(('2')) 
    
    def test_p2wpkh_key_generation(self):
        """Testa a geração de chaves para endereços P2WPKH (Segwit)"""
        request = KeyRequest(
            method="entropy",
            key_type="p2wpkh",
            network="testnet"
        )
        result = generate_key(request)
        
        assert result.address is not None
        assert result.address.startswith('tb1q')  
    
    def test_p2tr_key_generation(self):
        """Testa a geração de chaves para endereços P2TR (Taproot)"""
        request = KeyRequest(
            method="entropy",
            key_type="p2tr",
            network="testnet"
        )
        result = generate_key(request)
        
        assert result.address is not None
        assert result.address.startswith('tb1p')  
    
    def test_testnet_key_generations_all_formats(self):
        """Testa a geração de todos os formatos de chave para testnet"""
        entropy_request = KeyRequest(
            method="entropy",
            key_type="p2pkh",
            network="testnet"
        )
        p2pkh_result = generate_key(entropy_request)
        
        p2sh_request = KeyRequest(
            method="entropy",
            key_type="p2sh",
            network="testnet"
        )
        p2sh_result = generate_key(p2sh_request)
        
        p2wpkh_request = KeyRequest(
            method="entropy",
            key_type="p2wpkh",
            network="testnet"
        )
        p2wpkh_result = generate_key(p2wpkh_request)
        
        p2tr_request = KeyRequest(
            method="entropy",
            key_type="p2tr",
            network="testnet"
        )
        p2tr_result = generate_key(p2tr_request)
        
        assert p2pkh_result.address.startswith(('m', 'n'))  
        assert p2sh_result.address.startswith('2')   
        assert p2wpkh_result.address.startswith('tb1q')  
        assert p2tr_result.address.startswith('tb1p')
    
    def test_key_derivation_error_handling(self):
        """Testa o tratamento de erros na geração de chaves"""
        with pytest.raises(ValueError):
            invalid_network_request = KeyRequest(
                method="entropy",
                key_type="p2pkh",
                network="invalid_network"
            )
            generate_key(invalid_network_request)
        
        with pytest.raises(ValueError):
            invalid_type_request = KeyRequest(
                method="entropy",
                key_type="invalid_type",
                network="testnet"
            )
            generate_key(invalid_type_request)
