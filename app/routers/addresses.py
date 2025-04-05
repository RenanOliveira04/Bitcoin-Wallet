from fastapi import APIRouter, HTTPException, Query
from app.models.address_models import AddressFormat
from app.services.address_service import generate_address
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{address_format}", 
            summary="Gera um endereço Bitcoin no formato especificado",
            description="""
Gera um endereço Bitcoin em um dos formatos suportados a partir de uma chave privada.

## Formatos de Endereço Suportados:

1. **P2PKH (Legacy)** - `p2pkh`
   * Prefixo: `1` (mainnet) ou `m`/`n` (testnet)
   * Exemplo: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`
   * Compatível com todas as carteiras Bitcoin
   * Maior custo de transação, menos eficiente em espaço

2. **P2SH (SegWit encapsulado)** - `p2sh`
   * Prefixo: `3` (mainnet) ou `2` (testnet)
   * Exemplo: `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy`
   * Compatível com a maioria das carteiras
   * Formato de transição para SegWit, melhor que P2PKH

3. **P2WPKH (SegWit nativo)** - `p2wpkh`
   * Prefixo: `bc1q` (mainnet) ou `tb1q` (testnet)
   * Exemplo: `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4`
   * Mais eficiente em taxas, recomendado para uso atual
   * Requer carteiras com suporte a SegWit

4. **P2TR (Taproot)** - `p2tr`
   * Prefixo: `bc1p` (mainnet) ou `tb1p` (testnet)
   * Exemplo: `bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0`
   * Formato mais recente (ativado em Nov/2021)
   * Melhor privacidade e eficiência, suporte ainda limitado

## Parâmetros:

* **private_key**: Chave privada em formato WIF ou hexadecimal
* **address_format**: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
* **network**: Rede Bitcoin (testnet ou mainnet)

## Exemplo de resposta:
```json
{
  "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
  "format": "p2wpkh",
  "network": "testnet"
}
```
            """,
            response_description="Endereço Bitcoin no formato solicitado")
def get_address(
    private_key: str,
    address_format: AddressFormat,
    network: str = Query("testnet", description="mainnet ou testnet")
):
    """
    Gera um endereço Bitcoin no formato especificado
    
    - **private_key**: Chave privada em formato hexadecimal
    - **address_format**: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
    - **network**: Rede Bitcoin (mainnet ou testnet)
    """
    try:
        logger.info(f"Gerando endereço {address_format} para rede {network}")
        result = generate_address(private_key, address_format, network)
        return result
    except Exception as e:
        logger.error(f"Erro ao gerar endereço: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))