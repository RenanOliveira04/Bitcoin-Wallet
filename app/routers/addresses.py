from fastapi import APIRouter, HTTPException
from bitcoinlib.keys import Key
from app.dependencies import get_network

router = APIRouter()

@router.get("/{address_format}")
def generate_address(private_key: str, address_format: str):
    network = get_network()
    key = Key(private_hex=private_key)
    
    if address_format == "p2pkh":
        return {"address": key.address(script_type='p2pkh', network=network)}
    elif address_format == "p2wpkh":
        return {"address": key.address(script_type='p2wpkh', network=network)}
    else:
        raise HTTPException(status_code=400, detail="Formato inválido")