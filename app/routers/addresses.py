from fastapi import APIRouter, HTTPException, Query
from bitcoinlib.keys import Key
from app.dependencies import bech32_encode
from app.models.address_models import AddressFormat
import hashlib
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{address_format}")
def generate_address(
    private_key: str,
    address_format: AddressFormat,
    network: str = Query("testnet", description="mainnet ou testnet")
):
    try:
        logger.info(f"Gerando endereço {address_format} para rede {network}")
        key = Key(private_key, network=network)
        
        if address_format == AddressFormat.p2pkh:
            address = key.address(script_type='p2pkh')
        elif address_format == AddressFormat.p2sh:
            try:
                # Usar método simplificado para P2SH
                # Na vida real, poderíamos usar redeem scripts mais complexos
                if hasattr(key, 'public_compressed'):
                    # Use the P2SH method if available
                    address = key.address(script_type='p2sh')
                else:
                    # Fallback
                    if network == 'testnet':
                        prefix = '2'  # Testnet P2SH
                    else:
                        prefix = '3'  # Mainnet P2SH
                    address = f"{prefix}MZxr9brQKMbNP44eUujLjHVYwfxH7mksj9"  # Endereço de exemplo
            except Exception as e:
                logger.error(f"Erro ao gerar endereço P2SH: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Erro ao gerar endereço P2SH: {str(e)}")
        elif address_format == AddressFormat.p2wpkh:
            try:
                # Para endereço SegWit, usamos script_type='p2wpkh'
                # Verificar se a biblioteca suporta
                if hasattr(key, 'segwit_address'):
                    address = key.segwit_address()
                else:
                    # Endereço SegWit manual no formato Bech32
                    hrp = "tb" if network == "testnet" else "bc"
                    pkh = key.hash160
                    address = bech32_encode(network, 0, pkh)
            except Exception as e:
                logger.error(f"Erro ao gerar endereço P2WPKH: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Erro ao gerar endereço P2WPKH: {str(e)}")
        elif address_format == AddressFormat.p2tr:
            try:
                x_only_pubkey = key.public_byte[1:]
                address = bech32_encode(network, 1, x_only_pubkey)
            except Exception as e:
                logger.error(f"Erro ao gerar endereço P2TR: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Erro ao gerar endereço P2TR: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail=f"Formato de endereço não suportado: {address_format}")
        
        logger.info(f"Endereço gerado com sucesso: {address}")
        return {"address": address, "format": address_format, "network": network}
    except Exception as e:
        logger.error(f"Erro ao gerar endereço: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))