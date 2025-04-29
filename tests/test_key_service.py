import pytest
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos da aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app.services.key_service import (
    generate_keys, 
    validate_private_key, 
    derive_public_key, 
    derive_address,
    export_keys_to_file,
    create_keys_directory_if_not_exists
)

class TestKeyService:
    """Testes unitários para o serviço de chaves"""
    
    def test_generate_keys_with_entropy(self):
        """Testa geração de chaves usando método de entropia"""
        keys = generate_keys(method="entropy", network="testnet")
        
        assert keys is not None
        assert "private_key" in keys
        assert "public_key" in keys
        assert "address" in keys
        assert "network" in keys
        assert keys["network"] == "testnet"
        assert keys["private_key"].startswith("c") or keys["private_key"].startswith("9")
        
    def test_generate_keys_with_random(self):
        """Testa geração de chaves usando método aleatório"""
        keys = generate_keys(method="random", network="testnet")
        
        assert keys is not None
        assert "private_key" in keys
        assert "public_key" in keys
        assert "address" in keys
        assert "network" in keys
        assert keys["network"] == "testnet"
        
    def test_generate_keys_mainnet(self):
        """Testa geração de chaves na rede principal"""
        keys = generate_keys(method="entropy", network="mainnet")
        
        assert keys is not None
        assert "private_key" in keys
        assert "public_key" in keys
        assert "address" in keys
        assert "network" in keys
        assert keys["network"] == "mainnet"
        # Chaves privadas da mainnet geralmente começam com 5, K ou L
        assert keys["private_key"].startswith(("5", "K", "L"))
        
    def test_validate_private_key_valid(self):
        """Testa validação de chave privada válida"""
        # Chave privada WIF de testnet
        test_private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        result = validate_private_key(test_private_key, "testnet")
        
        assert result is True
        
    def test_validate_private_key_invalid(self):
        """Testa validação de chave privada inválida"""
        # Chave privada inválida
        invalid_private_key = "invalid_key_format"
        result = validate_private_key(invalid_private_key, "testnet")
        
        assert result is False
        
    def test_validate_private_key_wrong_network(self):
        """Testa validação de chave privada na rede errada"""
        # Chave privada WIF de testnet sendo validada como mainnet
        test_private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        result = validate_private_key(test_private_key, "mainnet")
        
        assert result is False
        
    def test_derive_public_key(self):
        """Testa derivação de chave pública a partir de chave privada"""
        test_private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        public_key = derive_public_key(test_private_key, "testnet")
        
        assert public_key is not None
        assert len(public_key) > 0
        
    def test_derive_address(self):
        """Testa derivação de endereço a partir de chave pública"""
        # Chave WIF e pública associada
        test_private_key = "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi"
        public_key = derive_public_key(test_private_key, "testnet")
        
        address = derive_address(public_key, "testnet")
        
        assert address is not None
        assert address.startswith(("m", "n", "2", "tb1"))  # Prefixos de testnet
        
    def test_create_keys_directory(self):
        """Testa criação do diretório para armazenar chaves"""
        directory = create_keys_directory_if_not_exists()
        
        assert directory is not None
        assert os.path.exists(directory)
        assert os.path.isdir(directory)
        
    def test_export_keys_to_file(self, tmp_path):
        """Testa exportação de chaves para arquivo"""
        # Criar diretório temporário para teste
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        
        # Dados para exportar
        key_data = {
            "private_key": "cTJVuFKuupCMvCTUhyeDf41aiagMXwW39MYQ6cvSgwXNVokHNuKi",
            "public_key": "02e2fcd9d80f35af180926bd94c81e3e79c3c2fd37d79ce4609f1bb36993f461e9",
            "address": "n1ZCXVKqxBBJFgdmwv5gqq8RyQBYcHxUKH",
            "network": "testnet"
        }
        
        # Exportar para formato TXT
        file_path = export_keys_to_file(
            key_data["private_key"],
            key_data["public_key"],
            key_data["address"],
            key_data["network"],
            "txt",
            str(keys_dir)
        )
        
        assert file_path is not None
        assert os.path.exists(file_path)
        
        # Verificar conteúdo do arquivo
        with open(file_path, 'r') as f:
            content = f.read()
            assert key_data["private_key"] in content
            assert key_data["public_key"] in content
            assert key_data["address"] in content
            assert key_data["network"] in content 