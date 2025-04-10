from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import BKeyError
from app.models.key_models import KeyResponse, KeyRequest
from app.dependencies import get_bitcoinlib_network, mask_sensitive_data
import logging

logger = logging.getLogger(__name__)

def generate_mnemonic():
    """
    Gera uma nova frase mnemônica BIP39 de 12 palavras.
    
    Returns:
        str: Frase mnemônica com 12 palavras em inglês separadas por espaço
    """
    return Mnemonic().generate()

def generate_key(request: KeyRequest) -> KeyResponse:
    """
    Gera um par de chaves Bitcoin (privada/pública) e endereço correspondente.
    
    Esta função suporta diferentes métodos de geração de chaves:
    
    1. Entropy: Gera uma chave aleatória usando entropia segura
    2. BIP39: Cria ou restaura uma chave a partir de uma frase mnemônica
    3. BIP32: Deriva uma chave a partir de uma chave mestre usando um caminho de derivação
    
    Os tipos de endereços suportados são:
    - P2PKH: Endereços Legacy (começam com 1 ou m/n)
    - P2SH: Endereços SegWit Compatíveis (começam com 3 ou 2)
    - P2WPKH: Endereços Native SegWit (começam com bc1 ou tb1)
    - P2TR: Endereços Taproot (começam com bc1p ou tb1p)
    
    Args:
        request (KeyRequest): Parâmetros para geração da chave, incluindo método, 
                             rede, mnemônico, caminho de derivação e senha
    
    Returns:
        KeyResponse: Objeto contendo chave privada, chave pública, endereço 
                    e metadados como formato, rede e caminho de derivação
        
    Raises:
        ValueError: Se ocorrer algum erro na geração das chaves ou
                   se o método de geração for inválido
    """
    try:
        network = request.network
        bitcoinlib_network = get_bitcoinlib_network(network)
            
        logger.info(f"[KEYS] Gerando chave na rede {network} usando método {request.method}")
        
        if request.method == "entropy":
            hdwallet = HDKey(network=bitcoinlib_network)
            derivation_path = None
            mnemonic = None
            logger.info("[KEYS] Nova chave gerada por entropia")
            
        elif request.method == "bip39":
            if not request.mnemonic:
                request.mnemonic = generate_mnemonic()
                logger.info("[KEYS] Novo mnemônico BIP39 gerado")
            else:
                logger.info(f"[KEYS] Usando mnemônico BIP39 fornecido: {mask_sensitive_data(request.mnemonic)}")
            
            hdwallet = HDKey.from_seed(
                seed=Mnemonic().to_seed(request.mnemonic, passphrase=request.passphrase),
                network=bitcoinlib_network
            )
            derivation_path = "m/0"
            mnemonic = request.mnemonic
            logger.info("[KEYS] Chave gerada a partir do mnemônico BIP39")
            
        elif request.method == "bip32":
            if not request.mnemonic:
                request.mnemonic = generate_mnemonic()
                logger.info("[KEYS] Novo mnemônico BIP32 gerado")
            else:
                logger.info(f"[KEYS] Usando mnemônico BIP32 fornecido: {mask_sensitive_data(request.mnemonic)}")
            
            if not request.derivation_path:
                logger.warning("[KEYS] Caminho de derivação não fornecido para método BIP32, usando padrão")
            
            master_key = HDKey.from_seed(
                seed=Mnemonic().to_seed(request.mnemonic, passphrase=request.passphrase),
                network=bitcoinlib_network
            )
            derivation_path = request.derivation_path or "m/44'/0'/0'/0/0"
            hdwallet = master_key.subkey_for_path(derivation_path)
            mnemonic = request.mnemonic
            logger.info(f"[KEYS] Chave derivada usando caminho: {derivation_path}")
        else:
            raise ValueError(f"Método de geração de chave inválido: {request.method}")
        
        key_format = request.key_format or "p2pkh"
        
        if key_format == "p2pkh":
            address = hdwallet.address()
        elif key_format == "p2sh":
            address = hdwallet.address_p2sh()
        elif key_format == "p2wpkh":
            address = hdwallet.address_segwit()
        elif key_format == "p2tr":
            try:
                address = hdwallet.address_taproot()
            except AttributeError:
                logger.warning("[KEYS] P2TR não disponível, usando P2WPKH como fallback")
                address = hdwallet.address_segwit()
                key_format = "p2wpkh"
        else:
            address = hdwallet.address()
            key_format = "p2pkh"
            
        logger.info(f"[KEYS] Endereço {key_format} gerado: {address}")
        
        return KeyResponse(
            private_key=hdwallet.wif() if hasattr(hdwallet, 'wif') else hdwallet.private_hex,
            public_key=hdwallet.public_hex,
            address=address,
            format=key_format,
            network=network,
            derivation_path=derivation_path,
            mnemonic=mnemonic
        )
    except BKeyError as e:
        logger.error(f"[KEYS] Erro nas chaves Bitcoin: {str(e)}")
        raise ValueError(f"Formato de chave inválido: {str(e)}")
    except Exception as e:
        logger.error(f"[KEYS] Erro ao gerar chaves: {str(e)}")
        raise ValueError(f"Erro ao gerar chaves: {str(e)}")