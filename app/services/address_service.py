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
        
        try:
            # Tenta carregar como WIF primeiro
            key = Key(private_key, network=bitcoinlib_network)
        except:
            # Se falhar, tenta carregar como hex
            try:
                key = HDKey.from_wif(private_key, network=bitcoinlib_network)
            except:
                # Se ainda falhar, tenta como HDKey
                key = HDKey(private_key, network=bitcoinlib_network)
        
        if address_format == "p2pkh":
            address = key.address()
        elif address_format == "p2sh":
            address = key.address_p2sh()
        elif address_format == "p2wpkh":
            address = key.address_segwit()
        elif address_format == "p2tr":
            try:
                address = key.address_taproot()
            except AttributeError:
                logger.warning("[ADDRESS] P2TR não disponível, usando P2WPKH como fallback")
                address = key.address_segwit()
                address_format = "p2wpkh"
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