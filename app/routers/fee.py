# app/routers/fee.py
from fastapi import APIRouter, Query, HTTPException
from app.models.fee_models import FeeEstimateModel
from app.services.fee_service import get_fee_estimate
from app.dependencies import get_network
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Taxas"],
    responses={
        400: {"description": "Requisição inválida"},
        500: {"description": "Erro ao consultar estimativa de taxas"}
    }
)

@router.get("/estimate", 
           summary="Estima a taxa ideal de transação",
           description="""
Estima a taxa de transação ideal com base nas condições atuais da rede Bitcoin, 
consultando APIs de mempool.

## Como as taxas funcionam no Bitcoin

As taxas no Bitcoin são calculadas em satoshis por byte virtual (sat/vB) ou 
satoshis por byte peso (sat/vByte). Transações com taxas mais altas são processadas 
mais rapidamente pelos mineradores.

## Níveis de prioridade:

* **Alta**: Para transações urgentes (~10-20 minutos)
* **Média**: Para transações normais (~1-3 blocos)
* **Baixa**: Para transações não-urgentes (~6+ blocos)
* **Mínima**: Taxa mínima para aceitação eventual

## Como as Taxas São Calculadas:

* O espaço nos blocos Bitcoin é limitado (aproximadamente 1MB por bloco)
* Os mineradores priorizam transações com taxas mais altas
* Em períodos de congestionamento, as taxas sobem devido à competição
* O mercado de taxas é dinâmico e pode mudar rapidamente

## Parâmetros:

* **priority**: Nível de prioridade (high, medium, low)
* **network**: Rede Bitcoin (mainnet ou testnet)

## Exemplo de resposta:
```json
{
  "high": 25.7,
  "medium": 15.2,
  "low": 8.9,
  "min": 1.1,
  "timestamp": 1650123456,
  "unit": "sat/vB"
}
```

## Observações:

* As estimativas são baseadas em condições atuais da rede
* As condições da rede podem mudar rapidamente
* Para transações mais urgentes, escolha prioridade "high"
* Taxa mínima (min) geralmente é suficiente para inclusão eventual
           """,
           response_model=FeeEstimateModel)
def estimate_fee(
    priority: str = Query(None, description="Nível de prioridade (high, medium, low)"), 
    network: str = Query(None, description="Rede Bitcoin (mainnet, testnet)")
):
    """
    Estima a taxa ideal para transações Bitcoin com base nas condições da rede.
    
    - **priority**: Nível de prioridade (high, medium, low)
    - **network**: Rede Bitcoin (mainnet, testnet)
    
    Retorna estimativas de taxa para diferentes níveis de prioridade.
    """
    try:
        network = network or get_network()
        result = get_fee_estimate(network)
        return result
    except Exception as e:
        logger.error(f"Erro ao estimar taxa: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao estimar taxa: {str(e)}")