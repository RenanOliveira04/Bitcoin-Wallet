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
- Estimativa de taxas baseada em condições da mempool
- Assinatura de transações
- Validação de transações
- Broadcast de transações
- Consulta de status de transações
- **Modo offline para uso como cold wallet**
- **Cache persistente de dados da blockchain**

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
# Crie e configure as branches
chmod +x scripts/setup_branches.sh
./scripts/setup_branches.sh

# Instale as dependências
pip install -r requirements.txt
```

3. Selecione o ambiente:
```bash
# Para desenvolvimento
cp config/development.env .env

# Para staging
cp config/staging.env .env

# Para produção
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
```

## Modo Cold Wallet

O Bitcoin Wallet Core pode ser usado como cold wallet, funcionando sem conexão constante com a internet:

```
OFFLINE_MODE=true
CACHE_DIR=/caminho/personalizado/cache
CACHE_TIMEOUT=2592000
```

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

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch a partir de `development`
3. Implemente suas alterações
4. Faça um Pull Request para a branch `development`

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 