from fastapi import APIRouter, HTTPException, Path, Query
from app.models.address_models import AddressFormat, AddressResponse
from app.services.address_service import generate_address
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Chaves e Endereços"],
    responses={
        400: {"description": "Requisição inválida"},
        500: {"description": "Erro interno do servidor"}
    }
)

@router.get("/{format}", 
            summary="Gera um endereço Bitcoin no formato especificado",
            description="""
Gera um endereço Bitcoin no formato especificado a partir de uma chave privada.

## Formatos de Endereços Suportados:

1. **P2PKH (Legacy)** - Pay to Public Key Hash
   * Prefixo: `1` (mainnet) ou `m/n` (testnet)
   * Exemplo: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`
   * Vantagens: Compatibilidade máxima com todas as carteiras
   * Desvantagens: Maior tamanho de transação e taxas mais altas

2. **P2SH (SegWit Compatível)** - Pay to Script Hash
   * Prefixo: `3` (mainnet) ou `2` (testnet)
   * Exemplo: `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy`
   * Vantagens: Compatível com a maioria das carteiras, taxas reduzidas
   * Desvantagens: Ainda não tão eficiente quanto o SegWit nativo

3. **P2WPKH (Native SegWit)** - Pay to Witness Public Key Hash
   * Prefixo: `bc1` (mainnet) ou `tb1` (testnet)
   * Exemplo: `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx`
   * Vantagens: Taxas significativamente menores, transações menores
   * Desvantagens: Algumas carteiras mais antigas podem não suportar

4. **P2TR (Taproot)** - Pay to Taproot
   * Prefixo: `bc1p` (mainnet) ou `tb1p` (testnet)
   * Exemplo: `bc1p6h5fuzmnvpdthf5shf0qqjzwy7wsqc5rhmgq2ks9xrak4ry6mtrscsqvzp`
   * Vantagens: Maior privacidade, contratos inteligentes mais eficientes
   * Desvantagens: Suporte limitado em carteiras (tecnologia mais recente)

## Parâmetros:

* **format**: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
* **private_key**: Chave privada em formato WIF ou hexadecimal
* **network**: Rede Bitcoin (mainnet ou testnet)

## Exemplos de Endereços (Testnet):

* **P2PKH**: `mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2`
* **P2SH**: `2N7SPBUArsbhbzGxzGXLiFc36T3MdFEwdZV`
* **P2WPKH**: `tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx`
* **P2TR**: `tb1p6h5fuzmnvpdthf5shf0qqjzwy7wsqc5rhmgq2ks9xrak4ry6mtrscsqvzp`

## Exemplo de resposta:
```json
{
  "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
  "format": "p2wpkh",
  "network": "testnet"
}
```

## Observações:

* P2WPKH (Native SegWit) oferece o melhor equilíbrio entre compatibilidade e eficiência
* P2TR (Taproot) é a tecnologia mais recente, com recursos avançados de privacidade
* Para máxima compatibilidade com carteiras antigas, use P2PKH
            """,
            response_model=AddressResponse)
def generate_address_from_key(
    format: AddressFormat = Path(..., description="Formato do endereço: p2pkh, p2sh, p2wpkh, p2tr"),
    private_key: str = Query(..., description="Chave privada em formato WIF ou hexadecimal"),
    network: str = Query(None, description="Rede Bitcoin (mainnet ou testnet)")
):
    """
    Gera um endereço Bitcoin no formato especificado a partir de uma chave privada.
    
    - **format**: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
    - **private_key**: Chave privada em formato WIF ou hexadecimal
    - **network**: Rede Bitcoin (mainnet ou testnet)
    
    Retorna o endereço gerado no formato especificado.
    """
    try:
        network = network or get_network()
        
        result = generate_address(
            private_key=private_key,
            address_format=format,
            network=network
        )
        
        return result
    except Exception as e:
        logger.error(f"Erro na geração de endereço: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))