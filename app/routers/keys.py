from fastapi import APIRouter, HTTPException
from app.models.key_models import KeyRequest, KeyResponse
from app.services.key_service import generate_key
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

@router.post("/", 
            summary="Gera novas chaves Bitcoin",
            description="""
Gera um novo par de chaves Bitcoin (privada/pública) e endereço correspondente
usando o método especificado.

## Métodos de Geração de Chaves:

1. **Entropy** (padrão): Gera uma chave completamente aleatória usando entropia segura
2. **BIP39**: Cria ou restaura uma chave a partir de uma frase mnemônica de 12-24 palavras
3. **BIP32**: Deriva uma chave a partir de uma chave mestre usando um caminho de derivação

## Geração BIP39 (Mnemônico):

As frases mnemônicas permitem:
* Backup fácil de chaves privadas (apenas palavras em inglês)
* Recuperação cross-wallet (compatível com outras carteiras)
* Múltiplas chaves derivadas de uma única semente

## Geração BIP32 (Derivação Hierárquica):

A derivação hierárquica permite:
* Gerar múltiplas chaves a partir de uma chave mestre
* Organizar chaves em uma estrutura de árvore hierárquica
* Criar carteiras HD (Hierarchical Deterministic) completas

## Tipos de Chaves Suportados:

* **P2PKH**: Endereços Legacy (começam com 1 ou m/n)
* **P2SH**: Endereços Segwit Compatíveis (começam com 3 ou 2)
* **P2WPKH**: Endereços Native Segwit (começam com bc1 ou tb1)
* **P2TR**: Endereços Taproot (começam com bc1p ou tb1p)

## Parâmetros:

* **method**: Método de geração (entropy, bip39, bip32)
* **network**: Rede Bitcoin (mainnet, testnet)
* **mnemonic**: Frase mnemônica para restauração (método bip39)
* **derivation_path**: Caminho de derivação BIP32 (método bip32)
* **passphrase**: Senha opcional para adicionar entropia

## Exemplo de resposta:
```json
{
  "private_key": "cVbZ9eQyCQKionG7J7xu5VLcKQzoubd6uv9pkzmfP24vRkXdLYGN",
  "public_key": "02a1633cafcc01ebfb6d78e39f687a1f0995c62fc95f51ead10a02ee0be551b5dc",
  "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
  "format": "p2pkh",
  "network": "testnet",
  "derivation_path": null,
  "mnemonic": null
}
```

## Segurança:

* **NUNCA compartilhe sua chave privada**
* Considere armazenar a frase mnemônica em local seguro
* Em produção, gere chaves em um ambiente offline quando possível
            """,
            response_model=KeyResponse)
def create_key(request: KeyRequest):
    """
    Gera um novo par de chaves Bitcoin e endereço correspondente.
    
    - **method**: Método de geração (entropy, bip39, bip32)
    - **network**: Rede Bitcoin (mainnet, testnet)
    - **mnemonic**: Frase mnemônica para restauração (método bip39)
    - **derivation_path**: Caminho de derivação BIP32 (método bip32)
    - **passphrase**: Senha opcional para adicionar entropia
    
    Retorna a chave privada, chave pública e endereço gerados.
    """
    try:
        network = request.network or get_network()
        
        result = generate_key(
            method=request.method,
            network=network,
            mnemonic=request.mnemonic,
            derivation_path=request.derivation_path,
            passphrase=request.passphrase
        )
        
        return result
    except Exception as e:
        logger.error(f"Erro na geração de chaves: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))