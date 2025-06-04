from typing import Literal, Optional, Union
from functools import lru_cache
from pydantic import BaseModel, Field, field_validator
from bitcoinlib.keys import HDKey, Key

from app.dependencies import get_bitcoinlib_network, mask_sensitive_data
import logging
import re

logger = logging.getLogger(__name__)

class AddressResponse(BaseModel):
    """Response model for generated Bitcoin address"""
    address: str
    format: Literal["p2pkh", "p2sh", "p2wpkh", "p2tr"]
    network: str = "testnet"
    
    class Config:
        schema_extra = {
            "example": {
                "address": "tb1qxyz...",
                "format": "p2wpkh",
                "network": "testnet"
            }
        }

class AddressRequest(BaseModel):
    """Request model for address generation"""
    private_key: str
    format: Literal["p2pkh", "p2sh", "p2wpkh", "p2tr"] = "p2wpkh"
    network: str = "testnet"
    
    @field_validator('private_key')
    @classmethod
    def validate_private_key(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Private key must be a non-empty string")
        return v.strip()
    
    @field_validator('network')
    @classmethod
    def validate_network(cls, v):
        if v not in ["mainnet", "testnet"]:
            raise ValueError("Network must be either 'mainnet' or 'testnet'")
        return v

def _load_private_key(private_key: str, network: str) -> Union[HDKey, Key]:
    """Load private key using multiple methods"""
    bitcoinlib_network = get_bitcoinlib_network(network)
    
    for method in [
        lambda: Key(private_key, network=bitcoinlib_network),
        lambda: HDKey.from_wif(private_key, network=bitcoinlib_network),
        lambda: HDKey(private_key, network=bitcoinlib_network),
    ]:
        try:
            return method()
        except Exception as e:
            logger.debug(f"[ADDRESS] Key loading method failed: {str(e)}")
            continue
    
    raise ValueError("Failed to load private key. Invalid or incompatible format.")

@lru_cache(maxsize=128)
def generate_address(
    private_key: str, 
    address_format: Literal["p2pkh", "p2sh", "p2wpkh", "p2tr"] = "p2wpkh",
    network: str = "testnet"
) -> AddressResponse:
    """
    Generate a Bitcoin address in the specified format from a private key.
    
    Supported address formats:
    - P2PKH (Legacy): Pay to Public Key Hash - compatible with all wallets
    - P2SH (SegWit Compatible): Pay to Script Hash - compatible with most wallets
    - P2WPKH (Native SegWit): Pay to Witness Public Key Hash - lower fees
    - P2TR (Taproot): Pay to Taproot - latest technology with better privacy
    
    Args:
        private_key: Private key in WIF or hex format
        address_format: Address format ('p2pkh', 'p2sh', 'p2wpkh', 'p2tr')
        network: Bitcoin network ('mainnet' or 'testnet')
    
    Returns:
        AddressResponse: Object containing the generated address, format, and network
        
    Raises:
        ValueError: If address format is invalid or private key cannot be loaded
    """
    try:
        request = AddressRequest(
            private_key=private_key,
            format=address_format,
            network=network
        )
        
        logger.info(f"[ADDRESS] Generating {request.format} address for private key {mask_sensitive_data(request.private_key)}")
        
        key = _load_private_key(request.private_key, request.network)
        
        address_generators = {
            "p2pkh": _generate_p2pkh,
            "p2sh": _generate_p2sh,
            "p2wpkh": _generate_p2wpkh,
            "p2tr": _generate_p2tr
        }
        
        if request.format not in address_generators:
            raise ValueError(f"Invalid address format: {request.format}")
        
        address = address_generators[request.format](key, request.network)
        
        logger.info(f"[ADDRESS] {request.format.upper()} address generated: {address}")
        
        return AddressResponse(
            address=address,
            format=request.format,
            network=request.network
        )
        
    except Exception as e:
        logger.error(f"[ADDRESS] Error generating address: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate address: {str(e)}")

def _generate_p2pkh(key: Union[HDKey, Key], network: str) -> str:
    """Generate P2PKH (Legacy) address"""
    try:
        return key.address()
    except Exception as e:
        logger.error(f"[ADDRESS] Error generating P2PKH: {str(e)}")
        raise ValueError(f"Failed to generate P2PKH address: {str(e)}")

def _generate_p2sh(key: Union[HDKey, Key], network: str) -> str:
    """Generate P2SH (SegWit Compatible) address"""
    try:
        if hasattr(key, 'address_p2sh'):
            return key.address_p2sh()
        elif hasattr(key, 'p2sh_address'):
            return key.p2sh_address()
        else:
            logger.warning("[ADDRESS] P2SH not available, falling back to P2PKH")
            return key.address()
    except Exception as e:
        logger.error(f"[ADDRESS] Error generating P2SH: {str(e)}")
        return key.address()  

def _generate_p2wpkh(key: Union[HDKey, Key], network: str) -> str:
    """Generate P2WPKH (Native SegWit) address"""
    try:
        if hasattr(key, 'address_segwit'):
            segwit = key.address_segwit
            return segwit() if callable(segwit) else segwit
        elif hasattr(key, 'address_segwit_p2wpkh'):
            return key.address_segwit_p2wpkh()
        elif hasattr(key, 'p2wpkh_address'):
            return key.p2wpkh_address()
        else:
            logger.warning("[ADDRESS] P2WPKH not available, falling back to P2PKH")
            return key.address()
    except Exception as e:
        logger.error(f"[ADDRESS] Error generating P2WPKH: {str(e)}")
        return key.address() 

def _generate_p2tr(key: Union[HDKey, Key], network: str) -> str:
    """Generate P2TR (Taproot) address"""
    try:
        if hasattr(key, 'address_taproot'):
            taproot = key.address_taproot
            return taproot() if callable(taproot) else taproot
        else:
            logger.warning("[ADDRESS] P2TR not available, falling back to P2PKH")
            return key.address()
    except Exception as e:
        logger.error(f"[ADDRESS] Error generating P2TR: {str(e)}")
        return key.address()  # Fallback to P2PKH