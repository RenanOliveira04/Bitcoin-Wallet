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
        network = request.network
        key_format = request.key_format
        
        # Correção para bitcoinlib reconhecer a rede
        if network == "mainnet":
            bitcoinlib_network = "bitcoin"
        else:
            bitcoinlib_network = network
            
        logger.info(f"Gerando chave na rede {network} com formato {key_format}")
        
        if request.method == "entropy":
            # Gerar nova chave aleatória
            hdwallet = HDKey(network=bitcoinlib_network)
            derivation_path = None
            mnemonic = None
            logger.info("Nova chave gerada por entropia")
            
        elif request.method == "bip39":
            # Se não forneceu mnemônico, gerar um novo
            if not request.mnemonic:
                request.mnemonic = generate_mnemonic()
                logger.info("Novo mnemônico BIP39 gerado")
            
            hdwallet = HDKey.from_seed(
                seed=Mnemonic().to_seed(request.mnemonic, password=request.password),
                network=bitcoinlib_network
            )
            derivation_path = "m/0"
            mnemonic = request.mnemonic
            logger.info("Chave gerada a partir do mnemônico BIP39")
            
        elif request.method == "bip32":
            # Se não forneceu mnemônico, gerar um novo
            if not request.mnemonic:
                request.mnemonic = generate_mnemonic()
                logger.info("Novo mnemônico BIP32 gerado")
            
            # Criar chave mestra a partir do mnemônico
            master_key = HDKey.from_seed(
                seed=Mnemonic().to_seed(request.mnemonic, password=request.password),
                network=bitcoinlib_network
            )
            # Derivar nova chave do caminho especificado
            hdwallet = master_key.subkey_for_path(request.derivation_path)
            derivation_path = request.derivation_path
            mnemonic = request.mnemonic
            logger.info(f"Chave derivada usando caminho: {request.derivation_path}")
        else:
            raise ValueError(f"Método de geração de chave inválido: {request.method}")
        
        # Gerar endereço no formato solicitado
        if key_format == "p2pkh":
            address = hdwallet.address()
            logger.info(f"Endereço P2PKH gerado: {address}")
        elif key_format == "p2sh":
            address = hdwallet.address_p2sh()
            logger.info(f"Endereço P2SH gerado: {address}")
        elif key_format == "p2wpkh":
            address = hdwallet.address_segwit()
            logger.info(f"Endereço P2WPKH gerado: {address}")
        elif key_format == "p2tr":
            # Verificar se a biblioteca suporta P2TR
            try:
                address = hdwallet.address_taproot()
                logger.info(f"Endereço P2TR gerado: {address}")
            except AttributeError:
                logger.warning("Biblioteca não suporta endereços P2TR, usando P2WPKH como fallback")
                address = hdwallet.address_segwit()
                key_format = "p2wpkh"  # Atualiza o formato real usado
        else:
            logger.warning(f"Formato de endereço desconhecido: {key_format}, usando P2PKH como padrão")
            address = hdwallet.address()
            key_format = "p2pkh"  # Atualiza o formato real usado
        
        return KeyResponse(
            private_key=hdwallet.private_hex,
            public_key=hdwallet.public_hex,
            address=address,
            format=key_format,
            network=network,
            derivation_path=derivation_path,
            mnemonic=mnemonic
        )
    except Exception as e:
        logger.error(f"Erro ao gerar chaves: {str(e)}")
        raise