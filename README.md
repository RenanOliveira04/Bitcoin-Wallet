# Bitcoin Wallet Core

Core da carteira Bitcoin que fornece uma API local para ser consumida por uma interface gráfica separada.

## Ambientes

O projeto possui três ambientes distintos:

### Development (desenvolvimento)
- Branch: `development`
- Rede: Testnet
- Logging: Nível DEBUG
- Cache: 60 segundos
- Uso: Desenvolvimento local e testes

### Staging (homologação)
- Branch: `staging`
- Rede: Testnet
- Logging: Nível INFO
- Cache: 300 segundos
- Uso: Testes de integração e homologação

### Production (produção)
- Branch: `production`
- Rede: Mainnet
- Logging: Nível WARNING
- Cache: 600 segundos
- Uso: Ambiente de produção

## Fluxo de Trabalho

1. Todo desenvolvimento deve ser feito na branch `development`
2. Para testar em staging:
   ```bash
   git checkout staging
   git merge development
   git push origin staging
   ```
3. Para deploy em produção:
   ```bash
   git checkout production
   git merge staging
   git push origin production
   ```

## Funcionalidades

- Geração de chaves Bitcoin (P2PKH, P2SH, P2WPKH, P2TR)
- Geração de endereços em diferentes formatos
- Consulta de saldo e UTXOs
- Construção de transações
  - Suporte a múltiplos formatos de transação
  - Builders: BitcoinLib e Bitcoin Core (python-bitcoinlib)
- Estimativa de taxas baseada em condições da mempool
- Assinatura de transações
- Validação de transações
- Broadcast de transações
- Consulta de status de transações
- **Modo offline para uso como cold wallet**
- **Cache persistente de dados da blockchain**
- **Armazenamento local de carteiras com SQLite**
  - Persistência de dados de carteiras
  - Histórico de transações
  - Rastreamento de UTXOs

## Builders de Transação

O sistema suporta múltiplos builders para criação de transações:

### BitcoinLibBuilder (padrão)
- Utiliza a biblioteca `bitcoinlib`
- Suporte completo a todos os tipos de transações
- Melhor para uso geral

### BitcoinCoreBuilder
- Utiliza a biblioteca `python-bitcoinlib`
- Compatível com Bitcoin Core
- Recomendado para aplicações que exigem alta compatibilidade com Bitcoin Core

Para selecionar o builder na API:
```
POST /api/tx/build?builder_type=bitcoincore
```

Para usar programaticamente:
```python
from app.models.utxo_models import TransactionRequest
from app.services.transaction import BitcoinCoreBuilder

builder = BitcoinCoreBuilder()
tx_response = builder.build(request, network="testnet")
```

## Requisitos

- Windows 10+ ou Linux
- Conexão com internet (exceto para modo offline)

## Instalação

### Usuários
1. Baixe o executável mais recente da [página de releases](https://github.com/seu-usuario/bitcoin-wallet/releases)
2. Execute o arquivo `bitcoin-wallet.exe` (Windows) ou `bitcoin-wallet` (Linux)
3. O servidor local iniciará automaticamente na porta 8000

### Desenvolvedores
1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bitcoin-wallet.git
cd bitcoin-wallet
```

2. Configure o ambiente:
```bash
chmod +x scripts/setup_branches.sh
./scripts/setup_branches.sh

pip install -r requirements.txt
```

3. Selecione o ambiente:
```bash
cp config/development.env .env

cp config/staging.env .env

cp config/production.env .env
```

4. Para gerar o executável:
```bash
python build.py
```

O executável será gerado na pasta `dist/`.

## Configuração

Cada ambiente possui seu próprio arquivo de configuração em `config/`:

- `development.env`: Configurações para desenvolvimento
- `staging.env`: Configurações para homologação
- `production.env`: Configurações para produção

## Uso com Frontend

O Bitcoin Wallet Core fornece uma API REST local que pode ser consumida por qualquer frontend. O servidor local roda em `http://127.0.0.1:8000` e aceita conexões apenas do localhost.

### Exemplo de Integração (JavaScript)
```javascript
const API_BASE = 'http://127.0.0.1:8000/api';

async function getBalance(address) {
  const response = await fetch(`${API_BASE}/balance/${address}`);
  return response.json();
}

// Exemplo de construção de transação com Bitcoin Core builder
async function buildTransaction(inputs, outputs, feeRate) {
  const response = await fetch(`${API_BASE}/tx/build?builder_type=bitcoincore`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      inputs: inputs,
      outputs: outputs,
      fee_rate: feeRate
    })
  });
  return response.json();
}

// Exemplo de uso do armazenamento local de carteiras
async function saveWallet(wallet) {
  const response = await fetch(`${API_BASE}/wallets`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(wallet)
  });
  return response.json();
}

async function getLocalWallets() {
  const response = await fetch(`${API_BASE}/wallets`);
  return response.json();
}

async function getWalletDetails(address) {
  const response = await fetch(`${API_BASE}/wallets/${address}`);
  return response.json();
}

async function getWalletTransactions(address) {
  const response = await fetch(`${API_BASE}/wallets/${address}/transactions`);
  return response.json();
}

async function getWalletUTXOs(address) {
  const response = await fetch(`${API_BASE}/wallets/${address}/utxos`);
  return response.json();
}
```

## Armazenamento Local com SQLite

O Bitcoin Wallet Core agora inclui uma camada de armazenamento local baseada em SQLite que permite:

- Salvar e gerenciar carteiras localmente
- Armazenar histórico de transações
- Rastrear UTXOs disponíveis
- Manter os dados mesmo sem conexão com a internet

O banco de dados SQLite é armazenado em `~/.bitcoin-wallet/data/wallet.db` e gerenciado automaticamente pelo aplicativo.

### Modelos de Dados

- **Wallet**: Armazena informações das carteiras (endereço, chave pública, formato, etc.)
- **Transaction**: Histórico de transações associadas a cada carteira
- **UTXO**: Rastreamento de UTXOs disponíveis para uso em transações

### Endpoints da API

- `GET /api/wallets`: Lista todas as carteiras salvas localmente
- `POST /api/wallets`: Salva uma nova carteira
- `GET /api/wallets/{address}`: Obtém detalhes de uma carteira específica
- `DELETE /api/wallets/{address}`: Remove uma carteira
- `GET /api/wallets/{address}/transactions`: Lista as transações de uma carteira
- `GET /api/wallets/{address}/utxos`: Lista os UTXOs de uma carteira

## Modo Cold Wallet

O Bitcoin Wallet Core pode ser usado como cold wallet, funcionando sem conexão constante com a internet:

```
OFFLINE_MODE=true
CACHE_DIR=/caminho/personalizado/cache
CACHE_TIMEOUT=2592000
```

O armazenamento local SQLite complementa o modo cold wallet, permitindo persistência de dados mesmo sem conectividade.

## Build e Distribuição

### Gerando o Executável
```bash
python build.py
```

### Docker (para desenvolvimento)
```bash
docker build -t bitcoin-wallet-core .
docker run -p 8000:8000 bitcoin-wallet-core
```

## Monitoramento

A aplicação inclui endpoints de health check e métricas:

- `GET /api/health`: Status do serviço
- `GET /api/metrics`: Métricas do sistema

### Monitoramento com Zabbix

O projeto inclui uma integração completa com Zabbix para monitoramento de desempenho, com as seguintes características:

#### Métricas Monitoradas

- **Health Check**: Verifica se a aplicação está online e saudável
- **Transações**: Contador de transações processadas
- **Saldo da Carteira**: Monitoramento do saldo atual
- **Tempo de Resposta**: Performance da API
- **Uso de CPU**: Consumo de CPU da aplicação
- **Uso de Memória**: Consumo de memória da aplicação
- **Requisições API**: Contador de chamadas à API
- **Taxa de Erro**: Percentual de erros nas requisições

#### Configuração do Zabbix

A configuração do Zabbix está disponível no diretório `/zabbix` e inclui:

- **Configurações do Agente**: Em `/zabbix/zabbix_agentd.d/`
- **Script de Coleta**: `/zabbix/collect_metrics.py`
- **Template Zabbix**: `/zabbix/bitcoin_wallet_template.xml`

#### Importando o Template

1. Acesse a interface web do Zabbix (disponível em http://localhost:80)
2. Vá para **Configuration > Templates**
3. Clique em **Import**
4. Selecione o arquivo `bitcoin_wallet_template.xml`
5. Clique em **Import**

#### Alertas Configurados

- **Aplicação Inativa**: Quando o health check falha
- **Tempo de Resposta Alto**: Quando o tempo de resposta excede 3 segundos
- **Alto Uso de CPU**: Quando o uso de CPU excede 80%
- **Alto Uso de Memória**: Quando o uso de memória excede 80%
- **Alta Taxa de Erro**: Quando a taxa de erro excede 5%

## Testes Unitários

O projeto utiliza `pytest` para testes unitários e `pytest-cov` para cobertura de código. Os testes cobrem os principais serviços e endpoints da aplicação.

### Estrutura de Testes

- `tests/conftest.py`: Fixtures compartilhadas entre os testes
- `tests/test_key_service.py`: Testes para o serviço de chaves
- `tests/test_address_service.py`: Testes para o serviço de endereços
- `tests/test_blockchain_service.py`: Testes para o serviço de blockchain
- `tests/test_health_router.py`: Testes para o router de health check
- `tests/test_api.py`: Testes de integração da API
- `tests/test_cold_wallet.py`: Testes de funcionalidades de cold wallet
- `tests/test_bitcoin_core_builder.py`: Testes para o builder de transações Bitcoin Core

### Executando os Testes

Para executar todos os testes:

```bash
python -m pytest
```

Para executar um arquivo de teste específico:

```bash
python -m pytest tests/test_key_service.py
```

Para verificar a cobertura de código:

```bash
python -m pytest --cov=app
```

Para gerar um relatório HTML de cobertura:

```bash
python -m pytest --cov=app --cov-report=html
```

### Implementando Novos Testes

Para implementar novos testes, crie um arquivo com o prefixo `test_` na pasta `tests/` seguindo as convenções do pytest. Use as fixtures disponíveis em `conftest.py` para compartilhar recursos comuns entre testes.

## API Documentation

### Base URL

```
http://localhost:8000/api
```

### Key Endpoints

#### Generate Bitcoin Keys

```
POST /api/keys
```

**Request Body:**
```json
{
  "method": "entropy|bip39|bip32",
  "network": "testnet|mainnet",
  "mnemonic": "optional mnemonic phrase",
  "passphrase": "optional passphrase",
  "derivation_path": "optional derivation path",
  "key_format": "p2pkh|p2sh|p2wpkh|p2tr"
}
```

**Response:**
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

**Important Notes:**
* When using `method: "bip39"`, ensure the mnemonic follows BIP39 standards
* For P2SH addresses, the implementation provides compatibility with both bitcoinlib 0.7.2 and higher

### Transaction Endpoints

#### Build Transaction

```
POST /api/tx/build?builder_type=bitcoinlib|bitcoincore
```

**Request Body:**
```json
{
  "inputs": [
    {
      "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
      "vout": 0,
      "value": 5000000,
      "address": "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
    }
  ],
  "outputs": [
    {
      "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
      "value": 4990000
    }
  ],
  "fee_rate": 2.0
}
```

**Response:**
```json
{
  "raw_transaction": "02000000013e283d571fe99cb1ebb0c012e0c8c8fb785d4a39e45d48636e67ea85dce01a7a0000000000ffffffff01e04b4c00000000001600142cd680318747b720d6d18a070cafab656bfb53b000000000",
  "txid": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z",
  "fee": 10000
}
```

**Important Notes:**
* The field name is `raw_transaction`, not `transaction_hex`
* The `builder_type` query parameter defaults to `bitcoinlib` if not specified
* The BitcoinCoreBuilder uses python-bitcoinlib 0.12.2 specifically 

### Wallet Storage Endpoints

#### Save Wallet

```
POST /api/wallets
```

**Request Body:**
```json
{
  "name": "My Test Wallet",
  "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
  "public_key": "02a1633cafcc01ebfb6d78e39f687a1f0995c62fc95f51ead10a02ee0be551b5dc",
  "format": "p2pkh",
  "network": "testnet",
  "derivation_path": null, 
  "mnemonic": null
}
```

**Response:**
```json
{
  "id": 1,
  "name": "My Test Wallet",
  "address": "mrS9zLDazNbgc5YDrLWuEhyPwbsKC8VHA2",
  "public_key": "02a1633cafcc01ebfb6d78e39f687a1f0995c62fc95f51ead10a02ee0be551b5dc",
  "format": "p2pkh",
  "network": "testnet",
  "derivation_path": null,
  "mnemonic": null,
  "created_at": "2025-06-01T20:30:00"
}
```

#### Get All Wallets

```
GET /api/wallets
```

#### Get Balance

```
GET /api/balance/{address}
```

**Response:**
```json
{
  "confirmed": 50000,
  "unconfirmed": 0,
  "total": 50000
}
```

### Error Handling

The API returns standard HTTP status codes:

* `200 OK` - Request successful
* `400 Bad Request` - Invalid input parameters
* `404 Not Found` - Resource not found
* `500 Internal Server Error` - Server-side error

Error responses include a detail message:

```json
{
  "detail": "Error message description"
}
```

For bitcoinlib-related errors, the detail message will include specific information about the error.

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch a partir de `development`
3. Implemente suas alterações
4. Faça um Pull Request para a branch `development`

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 