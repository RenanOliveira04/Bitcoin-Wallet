# Bitcoin Wallet para Desenvolvedores

Uma carteira Bitcoin voltada para desenvolvedores que permite acompanhar e entender todas as etapas do processo de criação e gerenciamento de chaves, endereços e transações Bitcoin.

## Sobre o Projeto

Esta carteira Bitcoin é compatível com MainNet e TestNet, permitindo:

- Geração e gerenciamento de chaves (Entropy, BIP39, BIP32)
- Criação de diferentes tipos de endereços Bitcoin
- Consulta de saldos e UTXOs
- Construção, assinatura e broadcast de transações
- Acompanhamento detalhado de cada etapa do processo

O diferencial é ser uma carteira focada em desenvolvedores, expondo os detalhes técnicos e permitindo maior controle sobre o processo.

## Pré-requisitos

- Python 3.9+
- pip (gerenciador de pacotes Python)
- Sistema operacional: Windows ou Linux

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bitcoin-wallet.git
cd bitcoin-wallet
```

2. Crie e ative um ambiente virtual:

No Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

No Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Crie um arquivo `.env` na raiz do projeto:
```env
NETWORK=testnet  # ou mainnet
BLOCKCHAIN_API_URL=https://api.blockchair.com/bitcoin
```

## Executando o Projeto

1. No Windows PowerShell:
```powershell
cd bitcoin-wallet
uvicorn app.main:app --reload
```

2. No Linux:
```bash
cd bitcoin-wallet
uvicorn app.main:app --reload
```

O servidor estará rodando em `http://localhost:8000`

## Documentação da API

Acesse a documentação Swagger UI em: `http://localhost:8000/docs`

## Exemplos de Uso

### 1. Gerando Chaves

#### Usando Entropia:
```bash
curl -X POST http://localhost:8000/api/keys \
-H "Content-Type: application/json" \
-d '{
  "method": "entropy",
  "network": "testnet"
}'
```

#### Usando BIP39 (com geração automática de mnemônico):
```bash
curl -X POST http://localhost:8000/api/keys \
-H "Content-Type: application/json" \
-d '{
  "method": "bip39",
  "network": "testnet"
}'
```

#### Usando BIP32 (com derivação de chaves):
```bash
curl -X POST http://localhost:8000/api/keys \
-H "Content-Type: application/json" \
-d '{
  "method": "bip32",
  "mnemonic": "seu mnemônico aqui",
  "derivation_path": "m/44'/1'/0'/0/0",
  "network": "testnet"
}'
```

### 2. Consultando Saldo
```bash
curl http://localhost:8000/api/balance/{endereco}
```

## Estrutura do Projeto
````├── app/
│ ├── routers/ # Endpoints REST
│ ├── models/ # Modelos Pydantic
│ ├── services/ # Lógica de negócio
│ └── dependencies.py # Configurações
├── tests/ # Testes
└── requirements.txt # Dependências
```

## Recursos Implementados

- [x] Geração de chaves (Entropy, BIP39, BIP32)
- [x] Geração de endereços
- [x] Consulta de saldos
- [ ] Construção de transações
- [ ] Assinatura de transações
- [ ] Broadcast de transações
- [ ] Consulta de status de transações

## Contribuindo

1. Fork o projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.