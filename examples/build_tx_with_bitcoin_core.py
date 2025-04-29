#!/usr/bin/env python
"""
Exemplo de uso do BitcoinCoreBuilder para construir uma transação Bitcoin.

Este script demonstra como usar o builder baseado em python-bitcoinlib (Bitcoin Core)
para construir uma transação Bitcoin não assinada.
"""

import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.utxo_models import TransactionRequest, Input, Output
from app.services.transaction import BitcoinCoreBuilder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Função principal que demonstra o uso do BitcoinCoreBuilder.
    """
    try:
        tx_request = TransactionRequest(
            inputs=[
                Input(
                    txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    vout=0,
                    value=5000000, 
                    address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
                )
            ],
            outputs=[
                Output(
                    address="tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    value=4990000 
                )
            ],
            fee_rate=2.0  
        )
        
        builder = BitcoinCoreBuilder()
        response = builder.build(tx_request, "testnet")
        
        print("=== Transação construída com sucesso ===")
        print(f"TXID: {response.txid}")
        print(f"Taxa: {response.fee} satoshis")
        print("\nTransação Raw (hex):")
        print(response.raw_transaction)
        
        print("\n=== Próximos passos ===")
        print("1. Assine a transação usando o endpoint /api/sign")
        print("2. Transmita a transação assinada usando o endpoint /api/broadcast")
        
    except Exception as e:
        logger.error(f"Erro ao construir transação: {str(e)}", exc_info=True)
        print(f"Erro: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 