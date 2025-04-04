# Bitcoin Wallet API
python test_api.py
API para gerenciamento de carteiras Bitcoin, suportando diferentes formatos de endereços e geração de chaves.

## Funcionalidades

- Geração de chaves Bitcoin (P2PKH, P2SH, P2WPKH, P2TR)
- Geração de endereços em diferentes formatos
- Consulta de saldo e UTXOs
- Construção de transações

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bitcoin-wallet.git
cd bitcoin-wallet
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (opcional):
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## Uso

1. Inicie o servidor:
```bash
uvicorn app.main:app --reload
```

2. Acesse a documentação da API:
```
http://localhost:8000/docs
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
  "network": "testnet"
}'
```

Resposta:
```json
{
  "private_key": "chave_privada_hex",
  "public_key": "chave_publica_hex",
  "address": "endereço_p2pkh",
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

## Configuração

A aplicação pode ser configurada através de variáveis de ambiente ou arquivo `.env`:

- `NETWORK`: Rede Bitcoin (mainnet ou testnet)
- `BLOCKCHAIN_API_URL`: URL da API de blockchain

## Dependências Principais

- `fastapi`: Framework web
- `bitcoinlib`: Biblioteca para manipulação de chaves e transações Bitcoin
- `bech32`: Biblioteca para codificação Bech32
- `pydantic`: Validação de dados
- `uvicorn`: Servidor ASGI

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 