import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.services.key_service import (
    generate_key,
    save_key_to_file,
    generate_mnemonic
)
from app.models.key_models import KeyRequest, KeyResponse

class TestKeyService:
    """Testes unitários para o serviço de chaves"""
    
    def test_generate_key_with_entropy(self):
        """Testa geração de chaves usando método de entropia"""
        request = KeyRequest(method="entropy", network="testnet")
        key_response = generate_key(request)
        
        assert key_response is not None
        assert key_response.private_key is not None
        assert key_response.public_key is not None
        assert key_response.address is not None
        assert key_response.network == "testnet"
        assert key_response.private_key.startswith("c") or key_response.private_key.startswith("9")
        
    def test_generate_key_with_bip39(self):
        """Testa geração de chaves usando método BIP39"""
        request = KeyRequest(method="bip39", network="testnet")
        key_response = generate_key(request)
        
        assert key_response is not None
        assert key_response.private_key is not None
        assert key_response.public_key is not None
        assert key_response.address is not None
        assert key_response.network == "testnet"
        assert key_response.mnemonic is not None
        
    def test_generate_key_mainnet(self):
        """Testa geração de chaves na rede principal"""
        request = KeyRequest(method="entropy", network="mainnet")
        key_response = generate_key(request)
        
        assert key_response is not None
        assert key_response.private_key is not None
        assert key_response.public_key is not None
        assert key_response.address is not None
        assert key_response.network == "mainnet"
        assert key_response.private_key.startswith(("5", "K", "L"))
        
    def test_generate_key_with_format(self):
        """Testa geração de chaves com formato específico"""
        request = KeyRequest(method="entropy", network="testnet", key_format="p2sh")
        key_response = generate_key(request)
        
        assert key_response is not None
        assert key_response.format == "p2sh"
        assert key_response.address.startswith("2") 
        
    def test_generate_mnemonic(self):
        """Testa geração de frase mnemônica"""
        mnemonic = generate_mnemonic()
        
        assert mnemonic is not None
        assert len(mnemonic.split()) == 12  
        
    def test_save_key_to_file(self, tmp_path):
        """Testa salvamento de chave em arquivo"""
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        
        request = KeyRequest(method="entropy", network="testnet")
        key_response = generate_key(request)
        
        file_path = save_key_to_file(key_response, str(keys_dir / "test_key.txt"))
        
        assert file_path is not None
        assert os.path.exists(file_path)
        
        with open(file_path, 'r') as f:
            content = f.read()
            assert key_response.private_key in content
            assert key_response.public_key in content
            assert key_response.address in content
            assert key_response.network in content 