from fastapi import APIRouter, Query
from app.services.fee_service import get_fee_estimate
from app.dependencies import get_network
from app.models.fee_models import FeeEstimateModel
import time

router = APIRouter()

@router.get("/estimate", 
          summary="Estimativa de taxa baseada na mempool atual",
          description="""
Retorna uma estimativa da taxa recomendada para transações Bitcoin baseada nas condições atuais da mempool.

## O que são taxas Bitcoin?

As taxas de transação no Bitcoin são pagas aos mineradores para incluir suas transações nos blocos.
Quando a rede está congestionada, transações com taxas mais altas são priorizadas.

## Níveis de Prioridade:

* **high**: Confirmação rápida (geralmente no próximo bloco, ~10 minutos)
* **medium**: Confirmação moderada (dentro de poucos blocos, ~30-60 minutos)
* **low**: Confirmação lenta (podendo levar várias horas)
* **min**: Taxa mínima aceitável (pode levar dias para confirmar)

## Unidades:

* **sat/vB**: Satoshis por byte virtual (unidade padrão após SegWit)
* **1 satoshi = 0.00000001 BTC**

## Como usar a estimativa de taxa?

Use o valor retornado no campo `fee_rate` ao construir uma transação.
Valores típicos variam de 1 a 100+ sat/vB dependendo da congestão da rede.

## Exemplo de resposta:
```json
{
  "timestamp": "2023-09-28T14:05:23Z",
  "fee_rates": {
    "high": 15.4,
    "medium": 8.2,
    "low": 3.5,
    "min": 1.0
  },
  "recommended": "medium",
  "mempool_size": 12541,
  "next_block_forecast": "< 10 minutos"
}
```

## Observações:

* As taxas podem variar drasticamente em curtos períodos
* Em mainnet, as taxas tendem a ser mais altas do que na testnet
* A estimativa é baseada em serviços externos (APIs de mempool)
* O valor é aproximado e não garante a inclusão no bloco
          """,
          response_description="Estimativa atual de taxas em satoshis por byte virtual (sat/vB)",
          response_model=FeeEstimateModel)
def estimate_fee(network: str = Query(None, description="Rede Bitcoin: mainnet ou testnet")):
    """
    Retorna a estimativa de taxa atual baseada nas condições da mempool.
    
    - **network**: Rede Bitcoin (mainnet ou testnet). 
                  Se não for fornecido, usa a configuração padrão.
    
    Retorna taxa em sat/vB para diferentes prioridades.
    """
    if not network:
        network = get_network()
        
    fee_data = get_fee_estimate(network)
    return FeeEstimateModel(
        high=fee_data['high_priority'],
        medium=fee_data['medium_priority'],
        low=fee_data['low_priority'],
        min=fee_data['fee_rate'],
        timestamp=int(time.time()),
        unit="sat/vB"
    ) 