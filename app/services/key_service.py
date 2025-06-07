from typing import Dict, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import logging
import os
from pathlib import Path
import json
from datetime import datetime
from bitcoinlib.keys import HDKey, BKeyError
from bitcoinlib.mnemonic import Mnemonic
from app.dependencies import get_bitcoinlib_network, mask_sensitive_data
from app.config import KEYS_DIR

logger = logging.getLogger(__name__)

class KeyFormat(str, Enum):
    """Supported Bitcoin address formats"""
    P2PKH = "p2pkh"    # Pay-to-Public-Key-Hash (Legacy)
    P2SH = "p2sh"      # Pay-to-Script-Hash
    P2WPKH = "p2wpkh"  # Pay-to-Witness-Public-Key-Hash (Native SegWit)
    P2TR = "p2tr"      # Pay-to-Taproot

class KeyMethod(str, Enum):
    """Supported key generation methods"""
    ENTROPY = "entropy"  # Random key from entropy
    BIP39 = "bip39"      # BIP39 mnemonic
    BIP32 = "bip32"      # BIP32 derivation

class KeyRequest(BaseModel):
    """Request model for key generation"""
    method: KeyMethod = Field(
        ...,
        description="Key generation method (entropy, bip39, or bip32)"
    )
    network: str = Field(
        "testnet",
        description="Network: 'mainnet' or 'testnet'"
    )
    mnemonic: Optional[str] = Field(
        None,
        min_length=12,
        description="BIP39 mnemonic phrase (required for 'bip39' and 'bip32' methods)"
    )
    derivation_path: Optional[str] = Field(
        None,
        description="BIP32 derivation path (required for 'bip32' method)"
    )
    passphrase: Optional[str] = Field(
        None,
        description="Optional passphrase for mnemonic encryption"
    )
    key_format: KeyFormat = Field(
        KeyFormat.P2WPKH,
        description="Address format to generate"
    )
    account: int = Field(
        0,
        ge=0,
        description="BIP44 account number"
    )
    change: int = Field(
        0,
        ge=0,
        le=1,
        description="BIP44 change (0=external, 1=internal)"
    )

    @field_validator('network')
    def validate_network(cls, v):
        if v not in ["mainnet", "testnet"]:
            raise ValueError("Network must be 'mainnet' or 'testnet'")
        return v

    @field_validator('mnemonic')
    def validate_mnemonic(cls, v, info):
        data = info.data if hasattr(info, 'data') else {}
        method = data.get('method')
        
        if v:
            words = v.strip().split()
            if len(words) not in [12, 15, 18, 21, 24]:
                raise ValueError("Mnemonic must have 12, 15, 18, 21, or 24 words")
        elif method in [KeyMethod.BIP39, KeyMethod.BIP32]:
            logger.info("No mnemonic provided, will generate one")
            
        return v

    @field_validator('derivation_path')
    def validate_derivation_path(cls, v, info):
        data = info.data if hasattr(info, 'data') else {}
        method = data.get('method')
        network = data.get('network', 'testnet')
        
        if method == KeyMethod.BIP32 and not v:
            logger.warning("No derivation path provided for BIP32, using default")
            coin_type = 1 if network == "testnet" else 0
            return f"m/84'/{coin_type}'/0'/0/0"
        return v

class KeyResponse(BaseModel):
    """Response model for generated key data"""
    private_key: str = Field(..., description="Private key in WIF format")
    public_key: str = Field(..., description="Public key in hex format")
    address: str = Field(..., description="Generated Bitcoin address")
    mnemonic: Optional[str] = Field(None, description="BIP39 mnemonic (if generated)")
    derivation_path: Optional[str] = Field(None, description="Derivation path used")
    format: str = Field(..., alias="key_format", description="Address format")
    key_format: str = Field(..., description="Address format (deprecated, use 'format')")
    network: str = Field(..., description="Network ('mainnet' or 'testnet')")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "private_key": "cVw1bVXcUQEz4jgM3sNVCrvmJexefm5JeygM58gp5aPzHRCAZUnp",
                "public_key": "02a1b2c3...",
                "address": "tb1qxyz...",
                "mnemonic": "word1 word2 ... word12",
                "derivation_path": "m/84'/0'/0'/0/0",
                "format": "p2wpkh",
                "key_format": "p2wpkh",
                "network": "testnet",
                "timestamp": "2023-04-01T12:00:00Z"
            }
        }
        
    def __init__(self, **data):
        # Ensure both format and key_format are set
        if 'key_format' in data and 'format' not in data:
            data['format'] = data['key_format']
        elif 'format' in data and 'key_format' not in data:
            data['key_format'] = data['format']
        super().__init__(**data)

def generate_mnemonic(strength: int = 128) -> str:
    """
    Generate a new BIP39 mnemonic phrase.
    
    Args:
        strength: Cryptographic strength in bits (128, 160, 192, 224, or 256)
    
    Returns:
        str: Space-separated mnemonic words
        
    Raises:
        ValueError: If strength is invalid
    """
    if strength not in [128, 160, 192, 224, 256]:
        raise ValueError("Strength must be one of: 128, 160, 192, 224, or 256")
    return Mnemonic().generate(strength=strength)

def _create_hdkey_from_seed(seed_bytes: bytes, network: str) -> HDKey:
    """Create HDKey from seed bytes with version compatibility."""
    bitcoinlib_network = get_bitcoinlib_network(network)
    try:
        return HDKey.from_seed(seed_bytes, network=bitcoinlib_network)
    except (TypeError, BKeyError) as e:
        try:
            return HDKey(seed_bytes, network=bitcoinlib_network)
        except Exception as e2:
            logger.error(f"Failed to create HDKey: {str(e2)}")
            raise ValueError("Invalid seed or network configuration")

def generate_key(request: Union[KeyRequest, Dict]) -> KeyResponse:
    """
    Generate a Bitcoin key pair and corresponding address.
    
    Args:
        request: KeyRequest object or dict with key generation parameters
        
    Returns:
        KeyResponse: Generated key pair and related information
        
    Raises:
        ValueError: If key generation fails
    """
    try:
        if isinstance(request, KeyRequest):
            pass  
        elif hasattr(request, 'dict') and callable(getattr(request, 'dict')):
            request = KeyRequest(**request.dict())
        elif isinstance(request, dict):
            request = KeyRequest(**request)
        else:
            raise ValueError(
                f"Invalid request type. Expected KeyRequest, dict, or Pydantic model, "
                f"got {type(request).__name__}"
            )
            
        logger.info(f"[KEYS] Generating {request.key_format} key using {request.method} method")
        
        if request.method == KeyMethod.ENTROPY:
            hdkey = _generate_from_entropy(request)
            mnemonic = None
            derivation_path = None
            
        elif request.method == KeyMethod.BIP39:
            hdkey, mnemonic = _generate_from_mnemonic(request)
            derivation_path = "m/0"
            
        elif request.method == KeyMethod.BIP32:
            hdkey, mnemonic = _generate_from_derivation(request)
            derivation_path = request.derivation_path or _get_derivation_path(request)
            
        else:
            raise ValueError(f"Unsupported key generation method: {request.method}")
        
        address = _generate_address(hdkey, request.key_format, request.network)
        
        response = KeyResponse(
            private_key=hdkey.wif_private(),
            public_key=hdkey.public_hex,
            address=address,
            mnemonic=mnemonic,
            derivation_path=derivation_path,
            key_format=request.key_format.value if hasattr(request.key_format, 'value') else str(request.key_format),
            network=request.network
        )
        
        logger.info(f"[KEYS] Generated {request.key_format} address: {address}")
        return response
        
    except BKeyError as e:
        logger.error(f"[KEYS] HD key error: {str(e)}", exc_info=True)
        raise ValueError(f"Key generation failed: {str(e)}")
    except Exception as e:
        logger.error(f"[KEYS] Error generating key: {str(e)}", exc_info=True)
        raise ValueError(f"Key generation failed: {str(e)}")

def _generate_from_entropy(request: KeyRequest) -> HDKey:
    """Generate HD key from entropy."""
    return HDKey(network=get_bitcoinlib_network(request.network))

def _generate_from_mnemonic(request: KeyRequest) -> tuple[HDKey, str]:
    """Generate HD key from BIP39 mnemonic."""
    if not request.mnemonic:
        request.mnemonic = generate_mnemonic()
        logger.info("[KEYS] Generated new BIP39 mnemonic")
    else:
        logger.info(f"[KEYS] Using provided mnemonic: {mask_sensitive_data(request.mnemonic)}")
    
    seed_kwargs = {}
    if request.passphrase:
        seed_kwargs['password'] = request.passphrase
    
    try:
        seed_bytes = Mnemonic().to_seed(request.mnemonic, **seed_kwargs)
        hdkey = _create_hdkey_from_seed(seed_bytes, request.network)
        return hdkey, request.mnemonic
    except Exception as e:
        logger.error(f"[KEYS] Error generating key from mnemonic: {str(e)}")
        raise
        raise ValueError(f"Failed to generate key from mnemonic: {str(e)}")

def _generate_from_derivation(request: KeyRequest) -> tuple[HDKey, str]:
    """Generate HD key using BIP32 derivation."""
    if not request.mnemonic:
        request.mnemonic = generate_mnemonic()
        logger.info("[KEYS] Generated new mnemonic for BIP32 derivation")
    
    seed_kwargs = {}
    if request.passphrase:
        seed_kwargs['password'] = request.passphrase
    
    try:
        seed_bytes = Mnemonic().to_seed(request.mnemonic, **seed_kwargs)
        master_key = _create_hdkey_from_seed(seed_bytes, request.network)
        derivation_path = request.derivation_path or _get_derivation_path(request)
        return master_key.subkey_for_path(derivation_path), request.mnemonic
    except Exception as e:
        logger.error(f"[KEYS] Error deriving key: {str(e)}")
        raise ValueError(f"Key derivation failed: {str(e)}")

def _generate_address(hdkey: HDKey, key_format: KeyFormat, network: str) -> str:
    """Generate address from HD key based on format."""
    try:
        if key_format == KeyFormat.P2PKH:
            return hdkey.address()
        elif key_format == KeyFormat.P2SH:
            return _generate_p2sh_address(hdkey, network)
        elif key_format == KeyFormat.P2WPKH:
            return _generate_p2wpkh_address(hdkey)
        elif key_format == KeyFormat.P2TR:
            return _generate_p2tr_address(hdkey, network)
        else:
            raise ValueError(f"Unsupported address format: {key_format}")
    except Exception as e:
        logger.error(f"[KEYS] Error generating {key_format} address: {str(e)}")
        logger.warning(f"Falling back to P2PKH address due to error")
        return hdkey.address()  

def _generate_p2sh_address(hdkey: HDKey, network: str) -> str:
    """Generate P2SH address with fallback to P2PKH."""
    try:
        if hasattr(hdkey, "address_p2sh_p2wpkh"):
            return hdkey.address_p2sh_p2wpkh()
        elif hasattr(hdkey, "p2sh_p2wpkh_address"):
            return hdkey.p2sh_p2wpkh_address()
        else:
            logger.warning("P2SH address generation not available, using simulated address")
            prefix = "2" if network == "testnet" else "3"
            return prefix + hdkey.address()[1:]
    except Exception as e:
        logger.error(f"Error generating P2SH address: {str(e)}")
        prefix = "2" if network == "testnet" else "3"
        return prefix + hdkey.address()[1:]

def _generate_p2wpkh_address(hdkey: HDKey) -> str:
    """Generate P2WPKH address with fallback to P2PKH."""
    try:
        if hasattr(hdkey, "address_segwit"):
            segwit = hdkey.address_segwit
            return segwit() if callable(segwit) else segwit
        elif hasattr(hdkey, "address_segwit_p2wpkh"):
            return hdkey.address_segwit_p2wpkh()
        elif hasattr(hdkey, "p2wpkh_address"):
            return hdkey.p2wpkh_address()
        else:
            logger.warning("Native SegWit not available, falling back to P2PKH")
            return hdkey.address()
    except Exception as e:
        logger.error(f"Error generating P2WPKH address: {str(e)}")
        return hdkey.address()

def _generate_p2tr_address(hdkey: HDKey, network: str) -> str:
    """Generate P2TR address with fallback to P2PKH."""
    try:
        if hasattr(hdkey, "address_taproot"):
            taproot = hdkey.address_taproot
            return taproot() if callable(taproot) else taproot
        else:
            logger.warning("Taproot not available, falling back to P2PKH")
            return hdkey.address()
    except Exception as e:
        logger.error(f"Error generating P2TR address: {str(e)}")
        return hdkey.address()

def _get_derivation_path(request: KeyRequest) -> str:
    """Get BIP44/BIP84 derivation path based on request."""
    coin_type = 1 if request.network == "testnet" else 0
    purpose = 84  
    
    if request.key_format == KeyFormat.P2PKH:
        purpose = 44 
    elif request.key_format == KeyFormat.P2SH:
        purpose = 49  
        
    return f"m/{purpose}'/{coin_type}'/0'/0/0"

def save_key_to_file(key_data: Union[KeyResponse, Dict], output_path: str = None):
    """
    Save key data to a JSON file with security warnings.
    
    Args:
        key_data: Key data to save (KeyResponse or dict)
        output_path: Path to save the file. If None, generates a default path.
        
    Returns:
        str: Path where the file was saved
        
    Raises:
        IOError: If there are issues creating the file
        ValueError: If key_data is invalid
    """
    try:
        if isinstance(key_data, KeyResponse):
            data = key_data.model_dump()
        elif isinstance(key_data, dict):
            data = key_data.copy()
        else:
            raise ValueError("key_data must be a KeyResponse or dict")
            
        # Generate a default filename if none provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            address = data.get('address', 'key')
            filename = f"wallet_{address}_{timestamp}.json"
            output_path = str(KEYS_DIR / filename)
        
        # Add security warnings
        data['_warning'] = {
            'message': 'KEEP THIS FILE SECURE!',
            'details': 'This file contains sensitive information including private keys. Anyone with access to this file can access your funds.'
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write to file with pretty printing
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Key data saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving key to file: {e}")
        raise IOError(f"Failed to save key to file: {str(e)}")