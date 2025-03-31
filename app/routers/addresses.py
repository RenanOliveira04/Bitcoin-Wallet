from fastapi import APIRouter, HTTPException, Query
from bitcoinlib.keys import Key
from app.dependencies import bech32_encode
from app.models.address_models import AddressFormat
import hashlib

router = APIRouter()

@router.get("/{address_format}")
def generate_address(
    private_key: str,
    address_format: AddressFormat,
    network: str = Query("testnet", description="mainnet ou testnet")
):
    try:
        key = Key(private_key)
        
        if address_format == AddressFormat.p2pkh:
            address = key.address(script_type='p2pkh', network=network)
        elif address_format == AddressFormat.p2sh:
            pubkey_hash = key.hash160()
            script = f"OP_0 {pubkey_hash.hex()}".encode()
            script_hash = hashlib.sha256(script).digest()
            address = Key(script_hash).address(script_type='p2sh', network=network)
        elif address_format == AddressFormat.p2wpkh:
            address = key.address(script_type='p2wpkh', network=network)
        elif address_format == AddressFormat.p2tr:
            x_only_pubkey = key.public_byte[1:]
            address = bech32_encode(network, 1, x_only_pubkey)
        
        return {"address": address, "format": address_format, "network": network}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))