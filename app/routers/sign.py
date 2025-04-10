from fastapi import APIRouter, HTTPException
from app.models.sign_models import SignRequest, SignResponse
from app.services.sign_service import sign_transaction
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", 
            summary="Assina uma transação Bitcoin",
            description="""
Assina uma transação Bitcoin usando a chave privada fornecida.

## Processo de Assinatura:

A assinatura de transações Bitcoin consiste em:
1. Verificar que a transação está corretamente formatada
2. Criar um hash de compromisso da transação para cada entrada (sighash)
3. Assinar cada hash com a chave privada correspondente
4. Incluir as assinaturas na estrutura da transação

## Detalhes importantes:

* A chave privada deve corresponder ao endereço que está gastando os UTXOs
* Bitcoin utiliza ECDSA (Elliptic Curve Digital Signature Algorithm) para assinaturas
* Transações SegWit (incluindo P2WPKH e P2TR) têm um processo de assinatura diferente 
  das transações Legacy (P2PKH)
* A assinatura é feita completamente no lado do cliente para segurança

## Parâmetros:

* **tx_hex**: Transação não assinada em formato hexadecimal
* **private_key**: Chave privada em formato WIF ou hexadecimal
* **network**: Rede Bitcoin (mainnet ou testnet)

## Exemplo de resposta:
```json
{
  "tx_hex": "0200000000010154f5a67cb14d7e50056f53263b72998c35e2f2acdbbe453d52c3b46c8e16a"
           + "6fe0000000000ffffffff01905f010000000000160014fd0c0f798a94620c260889b3fff0"
           + "b7dbd445e0b502483045022100f4e9bfc91f0cd516d65c4b4d001699a1272c9e274cde3b"
           + "da9c1292178d3dcfc2022009be6ced0fc4eae664174d508a04933a4a7e6687947aae0a"
           + "4d0848bcedbf743601210316de23a6c2dac233daddabc8de3f1bbd801da4171b0991"
           + "5cfc78e2354ebe6e9900000000",
  "txid": "a1b2c3d4e5f6...",
  "is_signed": true,
  "signatures_count": 1
}
```

## Segurança:

* **NUNCA envie chaves privadas pela rede em ambiente de produção!**
* A assinatura deve ser realizada offline em um ambiente seguro
* Esta API deve ser usada apenas para testes ou com quantias pequenas
            """,
            response_model=SignResponse)
def sign_tx(request: SignRequest):
    """
    Assina uma transação Bitcoin usando a chave privada fornecida.
    
    - **tx_hex**: Transação em formato hexadecimal
    - **private_key**: Chave privada em formato WIF ou hexadecimal
    - **network**: Rede Bitcoin (mainnet ou testnet)
    
    Retorna a transação assinada e informações sobre ela.
    """
    try:
        network = request.network or get_network()
        
        result = sign_transaction(
            tx_hex=request.tx_hex,
            private_key=request.private_key,
            network=network
        )
        
        return result
    except Exception as e:
        logger.error(f"Erro na rota de assinatura: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) 