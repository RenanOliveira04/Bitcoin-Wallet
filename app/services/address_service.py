from bitcoinlib.keys import HDKey, Key
from app.dependencies import bech32_encode
from typing import Optional, Tuple
import hashlib
import logging

logger = logging.getLogger(__name__)

def sha256(data: bytes) -> bytes:
    """Calcula o hash SHA256 dos dados"""
    return hashlib.sha256(data).digest()

def ripemd160(data: bytes) -> bytes:
    """Calcula o hash RIPEMD160 dos dados"""
    h = hashlib.new('ripemd160')
    h.update(data)
    return h.digest()

def hash160(data: bytes) -> bytes:
    """Calcula o hash HASH160 (RIPEMD160(SHA256(data)))"""
    return ripemd160(sha256(data))

def get_key_from_private(private_key: str, network: str) -> Tuple[Key, str]:
    """
    Obtém uma instância de Key a partir da chave privada
    
    Args:
        private_key: Chave privada em formato hexadecimal
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Tupla com (instância Key, rede bitcoinlib)
    """
    # Correção para bitcoinlib reconhecer a rede
    bitcoinlib_network = "bitcoin" if network == "mainnet" else network
    
    try:
        key = Key(private_key, network=bitcoinlib_network)
        return key, bitcoinlib_network
    except Exception as e:
        logger.error(f"Erro ao criar Key a partir da chave privada: {str(e)}")
        raise ValueError(f"Chave privada inválida: {str(e)}")

def generate_p2pkh_address(private_key: str, network: str) -> str:
    """
    Gera um endereço P2PKH (Legacy) a partir da chave privada
    
    Args:
        private_key: Chave privada em formato hexadecimal
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Endereço P2PKH (Legacy)
    """
    key, _ = get_key_from_private(private_key, network)
    try:
        address = key.address(script_type='p2pkh')
        logger.info(f"Endereço P2PKH gerado: {address}")
        return address
    except Exception as e:
        logger.error(f"Erro ao gerar endereço P2PKH: {str(e)}")
        raise ValueError(f"Não foi possível gerar o endereço P2PKH: {str(e)}")

def generate_p2sh_address(private_key: str, network: str) -> str:
    """
    Gera um endereço P2SH (Script Hash) a partir da chave privada
    
    Args:
        private_key: Chave privada em formato hexadecimal
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Endereço P2SH
    """
    key, _ = get_key_from_private(private_key, network)
    try:
        # Verificar se o método address_p2sh existe
        if hasattr(key, 'address_p2sh'):
            address = key.address_p2sh()
        else:
            # Fallback: tentar script_type
            address = key.address(script_type='p2sh')
            
        logger.info(f"Endereço P2SH gerado: {address}")
        return address
    except Exception as e:
        logger.error(f"Erro ao gerar endereço P2SH: {str(e)}")
        raise ValueError(f"Não foi possível gerar o endereço P2SH: {str(e)}")

def generate_p2wpkh_address(private_key: str, network: str) -> str:
    """
    Gera um endereço P2WPKH (SegWit) a partir da chave privada
    
    Args:
        private_key: Chave privada em formato hexadecimal
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Endereço P2WPKH (SegWit)
    """
    key, _ = get_key_from_private(private_key, network)
    try:
        # Primeiro tenta usar o método nativo da biblioteca
        if hasattr(key, 'segwit_address'):
            address = key.segwit_address()
        elif hasattr(key, 'address_segwit'):
            address = key.address_segwit()
        elif hasattr(key, 'address'):
            # Fallback: tentar script_type
            address = key.address(script_type='p2wpkh')
        else:
            # Implementação manual
            public_key_bytes = key.public_byte
            pubkey_hash = hash160(public_key_bytes)
            address = bech32_encode(network, 0, pubkey_hash)
            
        logger.info(f"Endereço P2WPKH gerado: {address}")
        return address
    except Exception as e:
        logger.error(f"Erro ao gerar endereço P2WPKH: {str(e)}")
        raise ValueError(f"Não foi possível gerar o endereço P2WPKH: {str(e)}")

def generate_p2tr_address(private_key: str, network: str) -> str:
    """
    Gera um endereço P2TR (Taproot) a partir da chave privada
    
    Args:
        private_key: Chave privada em formato hexadecimal
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Endereço P2TR (Taproot)
    """
    key, _ = get_key_from_private(private_key, network)
    try:
        # Primeiro tenta usar o método nativo da biblioteca
        if hasattr(key, 'address_taproot'):
            address = key.address_taproot()
        elif hasattr(key, 'address'):
            # Fallback: tentar script_type
            try:
                address = key.address(script_type='p2tr')
            except:
                # Implementação manual
                public_key_bytes = key.public_byte
                # Para Taproot, precisamos do x-only public key (sem o primeiro byte)
                x_only_pubkey = public_key_bytes[1:] if len(public_key_bytes) > 32 else public_key_bytes
                address = bech32_encode(network, 1, x_only_pubkey)
        else:
            # Implementação manual
            public_key_bytes = key.public_byte
            x_only_pubkey = public_key_bytes[1:] if len(public_key_bytes) > 32 else public_key_bytes
            address = bech32_encode(network, 1, x_only_pubkey)
            
        logger.info(f"Endereço P2TR gerado: {address}")
        return address
    except Exception as e:
        logger.error(f"Erro ao gerar endereço P2TR: {str(e)}")
        raise ValueError(f"Não foi possível gerar o endereço P2TR: {str(e)}")

def generate_address(private_key: str, address_format: str, network: str) -> dict:
    """
    Gera um endereço no formato especificado a partir da chave privada
    
    Args:
        private_key: Chave privada em formato hexadecimal
        address_format: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
        network: Rede Bitcoin (mainnet ou testnet)
        
    Returns:
        Dicionário com endereço, formato e rede
    """
    try:
        if address_format == "p2pkh":
            address = generate_p2pkh_address(private_key, network)
        elif address_format == "p2sh":
            address = generate_p2sh_address(private_key, network)
        elif address_format == "p2wpkh":
            address = generate_p2wpkh_address(private_key, network)
        elif address_format == "p2tr":
            address = generate_p2tr_address(private_key, network)
        else:
            raise ValueError(f"Formato de endereço não suportado: {address_format}")
            
        return {
            "address": address,
            "format": address_format,
            "network": network
        }
    except Exception as e:
        logger.error(f"Erro ao gerar endereço {address_format}: {str(e)}")
        raise 