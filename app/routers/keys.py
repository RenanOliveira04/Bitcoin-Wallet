from fastapi import APIRouter, HTTPException
from app.models.key_models import KeyRequest, KeyResponse
from app.services.key_service import generate_keys

router = APIRouter()

@router.post("/", response_model=KeyResponse, 
            summary="Gera novas chaves Bitcoin", 
            description="""
Cria um novo par de chaves Bitcoin (privada/pública) e seu endereço correspondente.

## Métodos de Geração Suportados:

* **entropy**: Gera uma chave completamente aleatória usando entropia do sistema
* **bip39**: Gera a partir de uma frase mnemônica (12/24 palavras) - se não fornecida, será gerada automaticamente
* **bip32**: Derivação determinística hierárquica a partir de uma seed ou caminho específico

## Parâmetros:

* **method**: Método de geração ('entropy', 'bip39', 'bip32')
* **mnemonic**: (Opcional) Frase mnemônica para recuperar chaves existentes
* **derivation_path**: (Opcional) Caminho de derivação BIP32, padrão: "m/44'/1'/0'/0/0" (testnet)
* **network**: Rede Bitcoin ('testnet' ou 'mainnet')
* **password**: (Opcional) Senha adicional para derivação da seed

## Exemplo de resposta:
```json
{
  "private_key": "cVbZ9eQyCQKionG7J7xu5VLcKQzoubd6uv9pkzmfP24vRkXdLYGN",
  "public_key": "03a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8d",
  "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
  "network": "testnet",
  "derivation_path": "m/44'/1'/0'/0/0",
  "mnemonic": "glass excess betray build gun intact calm calm broccoli disease calm voice"
}
```
            """,
            response_description="Novo par de chaves Bitcoin e seu endereço correspondente")
def create_keys(request: KeyRequest):
    """
    Gera um novo par de chaves Bitcoin (privada/pública) usando o método especificado.
    
    - **method**: Método de geração (entropy, bip39, bip32)
    - **mnemonic**: Opcional - Frase mnemônica para restaurar chaves existentes
    - **derivation_path**: Opcional - Caminho de derivação para BIP32
    - **network**: Rede Bitcoin (testnet, mainnet)
    """
    try:
        return generate_keys(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))