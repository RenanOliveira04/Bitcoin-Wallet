from bitcoinlib.keys import HDKey, Key
from app.models.address_models import AddressResponse
from app.dependencies import get_bitcoinlib_network, mask_sensitive_data
import logging

logger = logging.getLogger(__name__)

def generate_address(private_key: str, address_format: str = "p2wpkh", network: str = "testnet") -> AddressResponse:
    """
    Gera um endereço Bitcoin no formato especificado a partir de uma chave privada.
    
    Esta função suporta diferentes formatos de endereço:
    
    1. P2PKH (Legacy): Pay to Public Key Hash - compatível com todas as carteiras
    2. P2SH (SegWit Compatível): Pay to Script Hash - compatível com a maioria das carteiras
    3. P2WPKH (Native SegWit): Pay to Witness Public Key Hash - taxas menores
    4. P2TR (Taproot): Pay to Taproot - tecnologia mais recente com maior privacidade
    
    Args:
        private_key (str): Chave privada em formato WIF ou hexadecimal
        address_format (str): Formato do endereço ('p2pkh', 'p2sh', 'p2wpkh', 'p2tr')
        network (str): Rede Bitcoin ('mainnet', 'testnet')
    
    Returns:
        AddressResponse: Objeto contendo o endereço gerado, formato e rede
        
    Raises:
        ValueError: Se o formato do endereço for inválido ou a chave privada
            não puder ser carregada
    """
    try:
        bitcoinlib_network = get_bitcoinlib_network(network)
        logger.info(f"[ADDRESS] Gerando endereço {address_format} para chave privada {mask_sensitive_data(private_key)}")
        
        key = None
        for method in [
            lambda: Key(private_key, network=bitcoinlib_network),
            lambda: HDKey.from_wif(private_key, network=bitcoinlib_network),
            lambda: HDKey(private_key, network=bitcoinlib_network),
        ]:
            try:
                key = method()
                break
            except Exception as e:
                logger.debug(f"[ADDRESS] Método de carregamento de chave falhou: {str(e)}")
                continue
        
        if not key:
            raise ValueError(f"Não foi possível carregar a chave privada. Formato inválido ou incompatível.")
        
        if address_format == "p2pkh":
            try:
                address = key.address()
            except Exception as e:
                logger.error(f"[ADDRESS] Erro ao gerar P2PKH: {str(e)}")
                raise ValueError(f"Erro ao gerar endereço P2PKH: {str(e)}")
                
        elif address_format == "p2sh":
            try:
                if hasattr(key, 'address_p2sh'):
                    address = key.address_p2sh()
                elif hasattr(key, 'p2sh_address'):
                    address = key.p2sh_address()
                else:
                    logger.warning("[ADDRESS] P2SH não disponível, usando P2PKH como fallback")
                    address = key.address()
                    address_format = "p2pkh"
            except Exception as e:
                logger.error(f"[ADDRESS] Erro ao gerar P2SH: {str(e)}")
                address = key.address()
                address_format = "p2pkh"
                
        elif address_format == "p2wpkh":
            try:
                if hasattr(key, 'address_segwit'):
                    segwit_method = key.address_segwit
                    if callable(segwit_method):
                        address = segwit_method()
                    else:
                        address = segwit_method
                elif hasattr(key, 'address_segwit_p2wpkh'):
                    address = key.address_segwit_p2wpkh()
                elif hasattr(key, 'p2wpkh_address'):
                    address = key.p2wpkh_address()
                else:
                    logger.warning("[ADDRESS] P2WPKH não disponível, usando P2PKH como fallback")
                    address = key.address()
                    address_format = "p2pkh"
            except Exception as e:
                logger.error(f"[ADDRESS] Erro ao gerar P2WPKH: {str(e)}")
                address = key.address()
                address_format = "p2pkh"
                
        elif address_format == "p2tr":
            try:
                if hasattr(key, 'address_taproot'):
                    taproot_method = key.address_taproot
                    if callable(taproot_method):
                        address = taproot_method()
                    else:
                        address = taproot_method
                else:
                    logger.warning("[ADDRESS] P2TR não disponível, usando P2PKH como fallback")
                    address = key.address()
                    address_format = "p2pkh"
            except Exception as e:
                logger.error(f"[ADDRESS] Erro ao gerar P2TR: {str(e)}")
                address = key.address()
                address_format = "p2pkh"
        else:
            raise ValueError(f"Formato de endereço inválido: {address_format}")
        
        logger.info(f"[ADDRESS] Endereço {address_format} gerado: {address}")
        
        return AddressResponse(
            address=address,
            format=address_format,
            network=network
        )
        
    except Exception as e:
        logger.error(f"[ADDRESS] Erro ao gerar endereço: {str(e)}")
        raise ValueError(f"Erro ao gerar endereço: {str(e)}") 