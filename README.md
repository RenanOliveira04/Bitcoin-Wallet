# Bitcoin Wallet API

API para gerenciamento de carteiras Bitcoin, suportando diferentes formatos de endereços e geração de chaves.

## Funcionalidades

- Geração de chaves Bitcoin (P2PKH, P2SH, P2WPKH, P2TR)
- Geração de endereços em diferentes formatos
- Consulta de saldo e UTXOs
- Construção de transações
- Estimativa de taxas baseada em condições da mempool
- Assinatura de transações
- Validação de transações
- Broadcast de transações
- Consulta de status de transações

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/RenanOliveira04/bitcoin-wallet.git
cd bitcoin-wallet
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## Configuração (.env)

A API Bitcoin Wallet pode ser configurada através do arquivo `.env`. Este arquivo **não deve ser commitado no repositório** para proteger informações sensíveis.

### Configurações Básicas
```
# Valores possíveis: testnet, mainnet
NETWORK=testnet

# Valores possíveis: p2pkh, p2sh, p2wpkh, p2tr
DEFAULT_KEY_TYPE=p2wpkh

# Valores possíveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
LOG_FILE=bitcoin-wallet.log

# Tempo de cache em segundos
CACHE_TIMEOUT=300
```

### Configurações Sensíveis
Estas configurações podem conter informações sensíveis como URLs, chaves de API, etc., e devem ser mantidas em segurança:

```
# URLs das APIs (não commitar valores reais)
BLOCKCHAIN_API_URL=https://api.blockchair.com/bitcoin
MEMPOOL_API_URL=https://mempool.space/api

# Credenciais de API (se aplicável)
API_KEY=sua_chave_api
API_SECRET=seu_segredo_api
```

> **⚠️ IMPORTANTE:** 
> 1. Nunca commit seu arquivo `.env` no GitHub
> 2. O arquivo já está incluído no `.gitignore` para evitar vazamento de informações
> 3. Para ambientes de produção, considere usar um gerenciador de segredos ou variáveis de ambiente do sistema

## Uso

1. Inicie o servidor:
```bash
uvicorn app.main:app --reload
```

2. Acesse a documentação da API:
```
http://localhost:8000/redoc
```

3. Execute os testes:
```bash
# Opção 1: Modo interativo
python tests/test_api.py

# Opção 2: Especificando rede e formato de chave
python tests/test_api.py testnet p2wpkh

# Opção 3: Usar mainnet
python tests/test_api.py mainnet p2tr
```

## Endpoints

### Geração de Chaves

```bash
POST /api/keys
```

Gera uma nova chave Bitcoin usando diferentes métodos:
- `entropy`: Gera uma chave aleatória
- `bip39`: Gera uma chave a partir de uma frase mnemônica
- `bip32`: Gera uma chave derivada usando BIP32

Exemplo de requisição:
```bash
curl -X POST http://localhost:8000/api/keys \
-H "Content-Type: application/json" \
-d '{
  "method": "entropy",
  "network": "testnet",
  "key_format": "p2wpkh"
}'
```

Resposta:
```json
{
  "private_key": "chave_privada_hex",
  "public_key": "chave_publica_hex",
  "address": "endereço_p2wpkh",
  "format": "p2wpkh",
  "network": "testnet",
  "derivation_path": null,
  "mnemonic": null
}
```

### Geração de Endereços

```bash
GET /api/addresses/{format}
```

Gera um endereço Bitcoin no formato especificado a partir de uma chave privada.

#### Formatos Suportados:

1. **P2PKH (Legacy)**
   - Prefixo: `1` (mainnet) ou `m` (testnet)
   - Exemplo: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`
   - Uso: Compatível com todas as carteiras Bitcoin

2. **P2SH (SegWit)**
   - Prefixo: `3` (mainnet) ou `2` (testnet)
   - Exemplo: `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy`
   - Uso: Compatível com carteiras que suportam SegWit

3. **P2WPKH (Native SegWit)**
   - Prefixo: `bc1` (mainnet) ou `tb1` (testnet)
   - Exemplo: `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`
   - Uso: Carteiras modernas com suporte a SegWit nativo

4. **P2TR (Taproot)**
   - Prefixo: `bc1p` (mainnet) ou `tb1p` (testnet)
   - Exemplo: `bc1p...`
   - Uso: Carteiras com suporte a Taproot

#### Parâmetros:

- `private_key`: Chave privada em formato hexadecimal
- `format`: Formato do endereço (p2pkh, p2sh, p2wpkh, p2tr)
- `network`: Rede Bitcoin (mainnet ou testnet)

#### Exemplos de Requisição:

1. Gerar endereço P2PKH:
```bash
curl "http://localhost:8000/api/addresses/p2pkh?private_key=SUA_CHAVE_PRIVADA&network=testnet"
```

2. Gerar endereço P2SH:
```bash
curl "http://localhost:8000/api/addresses/p2sh?private_key=SUA_CHAVE_PRIVADA&network=testnet"
```

3. Gerar endereço P2WPKH:
```bash
curl "http://localhost:8000/api/addresses/p2wpkh?private_key=SUA_CHAVE_PRIVADA&network=testnet"
```

4. Gerar endereço P2TR (Taproot):
```bash
curl "http://localhost:8000/api/addresses/p2tr?private_key=SUA_CHAVE_PRIVADA&network=testnet"
```

#### Resposta:
```json
{
  "address": "endereço_gerado",
  "format": "formato_especificado",
  "network": "rede_especificada"
}
```

### Consulta de Saldo e UTXOs

```bash
GET /api/balance/{address}
```

Retorna o saldo e UTXOs disponíveis para um endereço.

Exemplo de requisição:
```bash
curl "http://localhost:8000/api/balance/tb1p..."
```

### Estimativa de Taxa

```bash
GET /api/fee/estimate
```

Estima a taxa ideal para transações com base nas condições atuais da mempool do Bitcoin.

#### Parâmetros:

- `priority` (opcional): Prioridade da transação (low, medium, high)
- `network` (opcional): Rede Bitcoin (mainnet ou testnet)

#### Exemplo de Requisição:
```bash
curl "http://localhost:8000/api/fee/estimate?priority=medium&network=testnet"
```

#### Resposta:
```json
{
  "fee_rate": 10.5,
  "priority": "medium",
  "unit": "sat/vB",
  "estimated_confirmation_time": "10-20 minutos"
}
```

### Construção de Transações

```bash
POST /api/utxo
```

Constrói uma transação Bitcoin a partir de UTXOs e saídas especificadas.

Exemplo de requisição:
```bash
curl -X POST http://localhost:8000/api/utxo \
-H "Content-Type: application/json" \
-d '{
  "inputs": [
    {
      "prev_tx": "txid",
      "output_n": 0,
      "script": "script",
      "value": 1000000
    }
  ],
  "outputs": [
    {
      "address": "endereço",
      "value": 900000
    }
  ],
  "fee_rate": 1
}'
```

### Assinatura de Transações

```bash
POST /api/sign
```

Assina uma transação com a chave privada fornecida.

#### Parâmetros (JSON):

- `tx_hex`: String hexadecimal da transação não assinada
- `private_key`: Chave privada para assinar
- `network` (opcional): Rede Bitcoin (mainnet ou testnet)

#### Exemplo de Requisição:
```bash
curl -X POST http://localhost:8000/api/sign \
-H "Content-Type: application/json" \
-d '{
  "tx_hex": "0200000001abcdef...",
  "private_key": "SUA_CHAVE_PRIVADA",
  "network": "testnet"
}'
```

#### Resposta:
```json
{
  "tx_hex": "0200000001abcdef...",
  "tx_hash": "1a2b3c4d...",
  "is_signed": true
}
```

### Validação de Transações

```bash
POST /api/validate
```

Valida a estrutura e os valores de uma transação Bitcoin.

#### Parâmetros (JSON):

- `tx_hex`: String hexadecimal da transação
- `network` (opcional): Rede Bitcoin (mainnet ou testnet)

#### Exemplo de Requisição:
```bash
curl -X POST http://localhost:8000/api/validate \
-H "Content-Type: application/json" \
-d '{
  "tx_hex": "0200000001abcdef...",
  "network": "testnet"
}'
```

#### Resposta:
```json
{
  "is_valid": true,
  "details": {
    "inputs_count": 1,
    "outputs_count": 2,
    "total_input": 1000000,
    "total_output": 990000,
    "fee": 10000
  }
}
```

### Consulta de Status de Transações

```bash
GET /api/tx/{txid}
```

Verifica o status atual de uma transação na blockchain.

#### Parâmetros:

- `txid`: ID da transação
- `network` (opcional): Rede Bitcoin (mainnet ou testnet)

#### Exemplo de Requisição:
```bash
curl "http://localhost:8000/api/tx/1a2b3c4d...?network=testnet"
```

#### Resposta:
```json
{
  "txid": "1a2b3c4d...",
  "status": "confirmed",
  "confirmations": 6,
  "block_height": 800000,
  "block_hash": "000000...",
  "timestamp": "2023-04-01T12:00:00Z",
  "explorer_url": "https://blockstream.info/testnet/tx/1a2b3c4d..."
}
```

## Configuração

A aplicação pode ser configurada através de variáveis de ambiente ou arquivo `.env`:

- `NETWORK`: Rede Bitcoin (mainnet ou testnet)
- `BLOCKCHAIN_API_URL`: URL da API de blockchain
- `MEMPOOL_API_URL`: URL da API Mempool.space para estimativa de taxa

## Dependências Principais

- `fastapi`: Framework web
- `bitcoinlib`: Biblioteca para manipulação de chaves e transações Bitcoin
- `bech32`: Biblioteca para codificação Bech32
- `pydantic`: Validação de dados
- `uvicorn`: Servidor ASGI
- `requests`: Cliente HTTP para APIs externas

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 