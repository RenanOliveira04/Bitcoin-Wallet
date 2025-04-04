import requests
import json
import sys
import traceback

BASE_URL = "http://localhost:8000/api"

def test_build_transaction():
    """Testa a construção de transações com detalhes de erro"""
    try:
        print("Construindo transação...")
        tx_request = {
            "inputs": [
                {
                    "txid": "abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
                    "vout": 0,
                    "value": 10000000  # 0.1 BTC em satoshis
                }
            ],
            "outputs": [
                {
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",  # Endereço de teste
                    "value": 9900000  # 0.099 BTC em satoshis (0.001 BTC para taxa)
                }
            ],
            "fee_rate": 1.0
        }
        print(f"Dados da requisição: {json.dumps(tx_request, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/utxo", json=tx_request)
        
        print(f"Status da resposta: {response.status_code}")
        print(f"Headers da resposta: {response.headers}")
        
        try:
            print(f"Corpo da resposta: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Corpo da resposta (texto): {response.text}")
            
        return response
    except Exception as e:
        print(f"Erro ao construir transação: {str(e)}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_build_transaction() 