from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic
from app.models.key_models import KeyResponse, KeyRequest
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def generate_mnemonic():
    """Gera uma nova frase mnemônica de 12 palavras"""
    return Mnemonic().generate()

def generate_keys(request: KeyRequest) -> KeyResponse:
    try:
        if request.method == "entropy":
            # Gerar nova chave aleatória
            hdwallet = HDKey()
            derivation_path = None
            mnemonic = None
            logger.info("Nova chave gerada por entropia")
            
        elif request.method == "bip39":
            # Se não forneceu mnemônico, gerar um novo
            if not request.mnemonic:
                request.mnemonic = generate_mnemonic()
                logger.info("Novo mnemônico BIP39 gerado")
            
            hdwallet = HDKey.from_seed(request.mnemonic)
            derivation_path = "m/0"
            mnemonic = request.mnemonic
            logger.info("Chave gerada a partir do mnemônico BIP39")
            
        elif request.method == "bip32":
            # Se não forneceu mnemônico, gerar um novo
            if not request.mnemonic:
                request.mnemonic = generate_mnemonic()
                logger.info("Novo mnemônico BIP32 gerado")
            
            # Criar chave mestra a partir do mnemônico
            master_key = HDKey.from_seed(request.mnemonic)
            # Derivar nova chave do caminho especificado
            hdwallet = master_key.subkey_for_path(request.derivation_path)
            derivation_path = request.derivation_path
            mnemonic = request.mnemonic
            logger.info(f"Chave derivada usando caminho: {request.derivation_path}")
        
        # Gerar endereço
        address = hdwallet.address()
        
        return KeyResponse(
            private_key=hdwallet.private_hex,
            public_key=hdwallet.public_hex,
            address=address,
            derivation_path=derivation_path,
            mnemonic=mnemonic  # Incluir o mnemônico na resposta
        )
    except Exception as e:
        logger.error(f"Erro ao gerar chaves: {str(e)}")
        raise