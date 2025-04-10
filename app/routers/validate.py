from fastapi import APIRouter, HTTPException
from app.models.validate_models import ValidateRequest, ValidateResponse
from app.services.validate_service import validate_transaction
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", 
            summary="Valida uma transação Bitcoin",
            description="""
Valida uma transação Bitcoin verificando sua estrutura, assinaturas e balanço de entrada/saída.

## O que é validado:

1. **Estrutura da Transação**:
   * Formato correto dos campos
   * Versão compatível 
   * Campos obrigatórios presentes

2. **Assinaturas**:
   * Verificação criptográfica das assinaturas (se presentes)
   * Correspondência entre chaves públicas e assinaturas

3. **Balanço de Valores**:
   * Total de entradas ≥ Total de saídas
   * Taxa de transação (diferença entre entradas e saídas) é razoável

4. **Conformidade com Regras**:
   * Tamanho dentro dos limites permitidos
   * Formatos de script válidos
   * Valores não negativos

## Parâmetros:

* **tx_hex**: Transação em formato hexadecimal (assinada ou não assinada)
* **network**: Rede Bitcoin (mainnet ou testnet)

## Exemplo de resposta para transação válida:
```json
{
  "is_valid": true,
  "details": {
    "version": 2,
    "locktime": 0,
    "inputs_count": 1,
    "outputs_count": 2,
    "total_input": 50000,
    "total_output": 49000,
    "fee": 1000,
    "is_signed": true,
    "estimated_size": 225,
    "estimated_fee_rate": 4.44
  }
}
```

## Exemplo de resposta para transação inválida:
```json
{
  "is_valid": false,
  "issues": [
    "Entrada insuficiente para cobrir saída: faltam 5000 satoshis",
    "Assinatura inválida na entrada 0"
  ],
  "details": {
    "version": 2,
    "inputs_count": 1,
    "outputs_count": 1,
    "total_input": 10000,
    "total_output": 15000,
    "fee": -5000,
    "is_signed": true
  }
}
```

## Observações:

* Uma transação pode ser estruturalmente válida mas ter assinaturas inválidas
* A validação não verifica se os UTXOs realmente existem na blockchain
* Uma transação "válida" localmente pode ser rejeitada pela rede por outras razões
            """,
            response_model=ValidateResponse)
def validate_tx(request: ValidateRequest):
    """
    Valida uma transação Bitcoin.
    
    - **tx_hex**: Transação em formato hexadecimal
    - **network**: Rede Bitcoin (testnet ou mainnet)
    
    Retorna resultado da validação, incluindo se a estrutura é válida 
    e se há saldo suficiente.
    """
    try:
        network = request.network or get_network()
        
        result = validate_transaction(
            tx_hex=request.tx_hex,
            network=network
        )
        
        return result
    except Exception as e:
        logger.error(f"Erro na rota de validação: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) 