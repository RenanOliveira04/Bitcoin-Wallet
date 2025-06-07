"""
Módulo de banco de dados para persistência local de dados de carteiras
"""
from .models import Base, Wallet, Transaction, UTXO
from .service import get_db, WalletDBService, TransactionDBService, UTXODBService, engine
