from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.keys import BKeyError
from app.models.key_models import KeyResponse, KeyRequest
from app.dependencies import get_bitcoinlib_network, mask_sensitive_data
import logging
import os
from datetime import datetime

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
            try:
                address = hdwallet.address_segwit
                if callable(address):
                    address = address()
            except (AttributeError, TypeError) as e:
                logger.warning(f"[KEYS] Método address_segwit não disponível: {str(e)}")
                try:
                    if hasattr(hdwallet, "address_segwit_p2wpkh"):
                        address = hdwallet.address_segwit_p2wpkh()
                    elif hasattr(hdwallet, "p2wpkh_address"):
                        address = hdwallet.p2wpkh_address()
                    else:
                        logger.warning("[KEYS] Fallback para P2PKH devido à incompatibilidade com SegWit")
                        address = hdwallet.address()
                        key_format = "p2pkh"
                except Exception as e2:
                    logger.error(f"[KEYS] Erro ao gerar endereço SegWit: {str(e2)}")
                    address = hdwallet.address()
                    key_format = "p2pkh"
        elif key_format == "p2tr":
            try:
                if hasattr(hdwallet, "address_taproot"):
                    address = hdwallet.address_taproot()
                else:
                    logger.warning("[KEYS] P2TR não disponível, usando P2PKH como fallback")
                    address = hdwallet.address()
                    key_format = "p2pkh"
            except AttributeError:
                logger.warning("[KEYS] P2TR não disponível, usando P2PKH como fallback")
                address = hdwallet.address()
                key_format = "p2pkh"
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

def save_key_to_file(key_data: KeyResponse, output_path: str = None) -> str:
    """
    Salva os detalhes da chave gerada em um arquivo de texto.
    
    Esta função cria um arquivo de texto com as informações da chave Bitcoin,
    incluindo chave privada, chave pública, endereço, formato e rede.
    O arquivo inclui avisos de segurança sobre a importância de manter
    a chave privada em segurança.
    
    Args:
        key_data (KeyResponse): Dados da chave gerada
        output_path (str, optional): Caminho onde o arquivo será salvo.
            Se None, será usado um caminho padrão com timestamp.
    
    Returns:
        str: Caminho completo do arquivo gerado
        
    Raises:
        IOError: Se houver problemas ao criar o arquivo
    """
    try:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.getcwd(), "keys")
            
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"bitcoin_key_{key_data.format}_{timestamp}.txt"
            output_path = os.path.join(output_dir, filename)
        
        key_dict = key_data.model_dump()
        
        content = [
            "=== BITCOIN WALLET - INFORMAÇÕES DA CHAVE ===",
            "AVISO DE SEGURANÇA: MANTENHA ESTE ARQUIVO EM LOCAL SEGURO!",
            "Qualquer pessoa com acesso à chave privada pode gastar seus bitcoins.",
            "",
            f"Data de Geração: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "INFORMAÇÕES DA CHAVE:",
            f"Rede: {key_dict['network']}",
            f"Formato: {key_dict['format']}",
            f"Endereço: {key_dict['address']}",
            "",
            "DADOS SENSÍVEIS - NÃO COMPARTILHE!",
            f"Chave Privada: {key_dict['private_key']}",
            f"Chave Pública: {key_dict['public_key']}",
        ]
        
        if key_dict.get('mnemonic'):
            content.append("")
            content.append("FRASE DE RECUPERAÇÃO (MNEMÔNICO):")
            content.append(f"{key_dict['mnemonic']}")
            
        if key_dict.get('derivation_path'):
            content.append("")
            content.append(f"Caminho de Derivação: {key_dict['derivation_path']}")
        
        content.extend([
            "",
            "INSTRUÇÕES DE RECUPERAÇÃO:",
            "1. Para recuperar seus fundos, importe a chave privada ou frase mnemônica em uma carteira Bitcoin compatível",
            "2. Você pode usar carteiras como BlueWallet, Electrum, ou Ledger Live",
            "3. Sempre teste com pequenas quantias antes de usar para valores significativos",
            "",
            "=== FIM DAS INFORMAÇÕES DA CHAVE ==="
        ])
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(content))
            
        logger.info(f"[KEYS] Arquivo de chave gerado com sucesso: {output_path}")
        return output_path
            
    except Exception as e:
        logger.error(f"[KEYS] Erro ao salvar dados da chave em arquivo: {str(e)}")
        raise IOError(f"Não foi possível salvar o arquivo da chave: {str(e)}")