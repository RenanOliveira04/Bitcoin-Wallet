from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import keys, addresses, balance, utxo, broadcast, fee, sign, validate, tx, health, wallets
from app.dependencies import get_settings
import logging
from fastapi.openapi.utils import get_openapi
import os
import sys
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

api_description = """
# Bitcoin Wallet API

API completa para gerenciamento de carteiras Bitcoin, oferecendo suporte a diferentes formatos de endereços, geração de chaves, 
e operações completas com transações.

## 🔑 Características Principais

* **Geração de Chaves Bitcoin**: Suporte a múltiplos métodos (entropy, BIP39, BIP32)
* **Múltiplos Formatos de Endereços**: Legacy (P2PKH), SegWit (P2SH), Native SegWit (P2WPKH) e Taproot (P2TR)
* **Operações com Transações**: Construção, assinatura, validação e transmissão
* **Consulta de Saldo e UTXOs**: Para qualquer endereço na rede
* **Estimativa de Taxas**: Baseada em condições da mempool atual
* **Verificação de Status**: Acompanhamento de transações na blockchain

## 🔧 Exemplos de Uso

### Fluxo Básico de Transação

1. **Gerar Chaves**:
   ```bash
   POST /api/keys
   ```

2. **Obter Saldo e UTXOs**:
   ```bash
   GET /api/balance/{endereço}
   ```

3. **Construir Transação**:
   ```bash
   POST /api/utxo
   ```

4. **Assinar Transação**:
   ```bash
   POST /api/sign
   ```

5. **Transmitir Transação**:
   ```bash
   POST /api/broadcast
   ```

6. **Verificar Status**:
   ```bash
   GET /api/tx/{txid}
   ```

## 📋 Redes Suportadas

* **Testnet**: Para testes sem usar bitcoins reais
* **Mainnet**: Para operações com bitcoins reais

## 🛡️ Segurança

* Chaves privadas são processadas apenas localmente
* Nenhuma chave privada é armazenada nos servidores
* Comunicação via HTTPS recomendada para uso em produção

## 🧪 Ambiente de Teste

Use a testnet para experimentar a API sem arriscar fundos reais.

## 📚 Requisitos Técnicos

* Python 3.8+
* Dependências detalhadas em `requirements.txt`
* Configurações via arquivo `.env` ou variáveis de ambiente

## 📝 Licença

Este projeto está licenciado sob a licença MIT.
"""

tags_metadata = [
    {
        "name": "Chaves e Endereços",
        "description": "Operações relacionadas a chaves privadas e endereços Bitcoin.",
    },
    {
        "name": "Consultas",
        "description": "Operações de consulta de saldo, UTXOs e status de transações.",
    },
    {
        "name": "Transações",
        "description": "Operações para criar, assinar, validar e transmitir transações.",
    },
    {
        "name": "Taxas",
        "description": "Operações relacionadas a taxas de transação.",
    },
    {
        "name": "Carteiras",
        "description": "Operações relacionadas a carteiras Bitcoin.",
    },
]

app = FastAPI(
    title="Bitcoin Wallet API",
    description="API local para gerenciamento de carteiras Bitcoin",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["info"]["contact"] = {
        "name": "Suporte Bitcoin Wallet API",
        "email": "suporte@bitcoin-wallet-api.com",
        "url": "https://github.com/RenanOliveira04/bitcoin-wallet",
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
        
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(keys.router, prefix="/api/keys", tags=["Chaves"])
app.include_router(addresses.router, prefix="/api/addresses", tags=["Endereços"])
app.include_router(balance.router, prefix="/api/balance", tags=["Saldo e UTXOs"])
app.include_router(utxo.router, prefix="/api/utxo", tags=["Transações"])
app.include_router(broadcast.router, prefix="/api/broadcast", tags=["Transações"])
app.include_router(fee.router, prefix="/api/fee", tags=["Taxas"])
app.include_router(sign.router, prefix="/api/sign", tags=["Transações"])
app.include_router(validate.router, prefix="/api/validate", tags=["Transações"])
app.include_router(tx.router, prefix="/api/tx", tags=["Status"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(wallets.router, prefix="/api/wallets", tags=["Carteiras"])

def resource_path(relative_path):
    """Obtém o caminho absoluto para recursos empacotados"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_server():
    """Inicia o servidor FastAPI"""
    try:
        port = int(os.getenv('PORT', '8000'))
        logger.info(f"Iniciando servidor na porta {port}")
        
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",  
            log_level="info",
            reload=False  
        )
        server = uvicorn.Server(config)
        server.run()
        
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()