from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from app.models.key_models import KeyRequest, KeyResponse, KeyFormat, Network
from app.services.key_service import generate_key, save_key_to_file
from app.dependencies import get_network, get_default_key_type
import logging
import os
from pathlib import Path

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
        # Definir valores padrão se não fornecidos
        if not request.network:
            request.network = get_network()
        if not request.key_format:
            request.key_format = get_default_key_type()
        
        result = generate_key(request)
        return result
    except Exception as e:
        logger.error(f"[KEYS] Erro na geração de chaves: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/export", 
            summary="Gera chaves Bitcoin e exporta para arquivo de texto",
            description="""
Gera um novo par de chaves Bitcoin e salva as informações em um arquivo de texto para backup.

## Segurança Importante:

* **⚠️ Este arquivo contém sua chave privada!** Qualquer pessoa com acesso a este arquivo pode gastar seus bitcoins.
* **⚠️ Armazene-o em um local seguro**, preferencialmente offline.
* **⚠️ Considere criptografar o arquivo** para maior segurança.
* **⚠️ Faça backup** em múltiplos locais seguros.

## Conteúdo do Arquivo:

O arquivo exportado contém todas as informações necessárias para recuperar sua carteira:

* Endereço Bitcoin
* Chave privada
* Chave pública 
* Frase mnemônica (se aplicável)
* Caminho de derivação (se aplicável)
* Informações sobre a rede e formato

## Recuperação:

Para utilizar suas chaves no futuro, você pode:

1. Importar a chave privada em qualquer carteira Bitcoin compatível
2. Importar a frase mnemônica em carteiras que suportam BIP39
3. Utilizar a API `/api/keys` com o método "bip39" e a mnemônica salva

## Parâmetros:

Mesmos parâmetros da geração de chaves normal, com opção de especificar o caminho de saída.
            """)
def export_key_to_file(
    request: KeyRequest,
    background_tasks: BackgroundTasks,
    output_path: str = Query(None, description="Caminho opcional para salvar o arquivo de chaves")
):
    try:
        # Definir valores padrão se não fornecidos
        if not request.network:
            request.network = get_network()
        if not request.key_format:
            request.key_format = get_default_key_type()
        
        # Gerar a chave
        key_result = generate_key(request)
        
        # Salvar a chave em arquivo
        file_path = save_key_to_file(key_result, output_path)
        
        # Retornar o arquivo como download
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/plain",
            background=background_tasks
        )
    except Exception as e:
        logger.error(f"[KEYS] Erro ao exportar chaves: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))