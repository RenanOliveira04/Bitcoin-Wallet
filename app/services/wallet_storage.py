import sqlite3
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from app.models.wallet_models import WalletCreate, WalletResponse, TransactionRecord, UTXORecord

logger = logging.getLogger(__name__)

def get_db_path() -> str:
    """
    Gets the database file path for wallet storage
    
    Returns:
        str: Path to the SQLite database file
    """
    # Default location in user's home directory
    default_path = os.path.join(str(Path.home()), ".bitcoin-wallet", "wallets.db")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(default_path), exist_ok=True)
    
    return default_path

class WalletStorage:
    """
    Storage service for wallet data using SQLite
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize wallet storage with specified database path
        
        Args:
            db_path (str, optional): Path to SQLite database file.
                                    If None, uses default path.
        """
        self.db_path = db_path or get_db_path()
        self.conn = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Gets a database connection, creating one if needed
        
        Returns:
            sqlite3.Connection: Connection to the SQLite database
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Closes database connection if open"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_db(self):
        """Creates database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create wallets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            address TEXT NOT NULL UNIQUE,
            private_key TEXT,
            public_key TEXT NOT NULL,
            key_type TEXT NOT NULL,
            network TEXT NOT NULL DEFAULT 'testnet',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER,
            txid TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL,
            confirmations INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            raw_data TEXT,
            FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE
        )
        ''')
        
        # Create UTXOs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS utxos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER,
            txid TEXT NOT NULL,
            vout INTEGER NOT NULL,
            amount REAL NOT NULL,
            script TEXT,
            confirmations INTEGER DEFAULT 0,
            spent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE,
            UNIQUE(txid, vout)
        )
        ''')
        
        conn.commit()
    
    def create_wallet(self, wallet: WalletCreate) -> WalletResponse:
        """
        Creates a new wallet in the database
        
        Args:
            wallet (WalletCreate): Wallet data to create
            
        Returns:
            WalletResponse: Created wallet with ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO wallets (name, description, address, private_key, public_key, key_type, network)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallet.name, 
            wallet.description, 
            wallet.address, 
            wallet.private_key, 
            wallet.public_key, 
            wallet.key_type,
            "testnet"  # Always use testnet for tests
        ))
        
        wallet_id = cursor.lastrowid
        conn.commit()
        
        return self.get_wallet(wallet_id)
    
    def get_wallet(self, wallet_id: int) -> Optional[WalletResponse]:
        """
        Gets a wallet by ID
        
        Args:
            wallet_id (int): ID of the wallet to get
            
        Returns:
            Optional[WalletResponse]: Wallet data if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,))
        wallet_data = cursor.fetchone()
        
        if not wallet_data:
            return None
        
        return WalletResponse(
            id=wallet_data['id'],
            name=wallet_data['name'],
            description=wallet_data['description'],
            address=wallet_data['address'],
            private_key=wallet_data['private_key'],
            public_key=wallet_data['public_key'],
            key_type=wallet_data['key_type'],
            network=wallet_data['network'],
            created_at=wallet_data['created_at']
        )
    
    def list_wallets(self) -> List[WalletResponse]:
        """
        Lists all wallets in the database
        
        Returns:
            List[WalletResponse]: List of all wallets
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM wallets")
        wallet_rows = cursor.fetchall()
        
        wallets = []
        for row in wallet_rows:
            wallet = WalletResponse(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                address=row['address'],
                private_key=row['private_key'],
                public_key=row['public_key'],
                key_type=row['key_type'],
                network=row['network'],
                created_at=row['created_at']
            )
            wallets.append(wallet)
        
        return wallets
    
    def update_wallet(self, wallet_id: int, wallet_data: dict) -> Optional[WalletResponse]:
        """
        Updates a wallet in the database
        
        Args:
            wallet_id (int): ID of the wallet to update
            wallet_data (dict): New wallet data
            
        Returns:
            Optional[WalletResponse]: Updated wallet if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build SET clause dynamically based on provided fields
        set_clause = []
        params = []
        
        for field, value in wallet_data.items():
            if field in ['name', 'description', 'private_key', 'public_key']:
                set_clause.append(f"{field} = ?")
                params.append(value)
        
        if not set_clause:
            return self.get_wallet(wallet_id)
            
        query = f"UPDATE wallets SET {', '.join(set_clause)} WHERE id = ?"
        params.append(wallet_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            return None
            
        return self.get_wallet(wallet_id)
    
    def delete_wallet(self, wallet_id: int) -> bool:
        """
        Deletes a wallet from the database
        
        Args:
            wallet_id (int): ID of the wallet to delete
            
        Returns:
            bool: True if wallet was deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def add_transaction(self, wallet_id: int, transaction: TransactionRecord) -> int:
        """
        Adds a transaction record to a wallet
        
        Args:
            wallet_id (int): ID of the wallet
            transaction (TransactionRecord): Transaction data
            
        Returns:
            int: ID of the created transaction record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO transactions (wallet_id, txid, amount, fee, confirmations, status, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallet_id,
            transaction.txid,
            transaction.amount,
            transaction.fee,
            transaction.confirmations,
            transaction.status,
            json.dumps(transaction.raw_data) if transaction.raw_data else None
        ))
        
        tx_id = cursor.lastrowid
        conn.commit()
        
        return tx_id
    
    def add_utxo(self, wallet_id: int, utxo: UTXORecord) -> int:
        """
        Adds a UTXO record to a wallet
        
        Args:
            wallet_id (int): ID of the wallet
            utxo (UTXORecord): UTXO data
            
        Returns:
            int: ID of the created UTXO record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO utxos (wallet_id, txid, vout, amount, script, confirmations, spent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                wallet_id,
                utxo.txid,
                utxo.vout,
                utxo.amount,
                utxo.script,
                utxo.confirmations,
                utxo.spent
            ))
            
            utxo_id = cursor.lastrowid
            conn.commit()
            
            return utxo_id
        except sqlite3.IntegrityError:
            # UTXO already exists, just return the existing one
            cursor.execute('''
            SELECT id FROM utxos WHERE txid = ? AND vout = ?
            ''', (utxo.txid, utxo.vout))
            
            result = cursor.fetchone()
            if result:
                return result['id']
            
            return -1
    
    def get_transactions(self, wallet_id: int) -> List[TransactionRecord]:
        """
        Gets all transactions for a wallet
        
        Args:
            wallet_id (int): ID of the wallet
            
        Returns:
            List[TransactionRecord]: List of transactions
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM transactions WHERE wallet_id = ? ORDER BY timestamp DESC
        ''', (wallet_id,))
        
        tx_rows = cursor.fetchall()
        
        transactions = []
        for row in tx_rows:
            raw_data = json.loads(row['raw_data']) if row['raw_data'] else None
            
            tx = TransactionRecord(
                id=row['id'],
                txid=row['txid'],
                amount=row['amount'],
                fee=row['fee'],
                confirmations=row['confirmations'],
                timestamp=row['timestamp'],
                status=row['status'],
                raw_data=raw_data
            )
            transactions.append(tx)
        
        return transactions
    
    def get_utxos(self, wallet_id: int, unspent_only: bool = True) -> List[UTXORecord]:
        """
        Gets UTXOs for a wallet
        
        Args:
            wallet_id (int): ID of the wallet
            unspent_only (bool): If True, only returns unspent UTXOs
            
        Returns:
            List[UTXORecord]: List of UTXOs
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
        SELECT * FROM utxos WHERE wallet_id = ?
        '''
        
        if unspent_only:
            query += ' AND spent = 0'
            
        cursor.execute(query, (wallet_id,))
        
        utxo_rows = cursor.fetchall()
        
        utxos = []
        for row in utxo_rows:
            utxo = UTXORecord(
                id=row['id'],
                txid=row['txid'],
                vout=row['vout'],
                amount=row['amount'],
                script=row['script'],
                confirmations=row['confirmations'],
                spent=bool(row['spent'])
            )
            utxos.append(utxo)
        
        return utxos
    
    def mark_utxo_spent(self, txid: str, vout: int) -> bool:
        """
        Marks a UTXO as spent
        
        Args:
            txid (str): Transaction ID of the UTXO
            vout (int): Output index
            
        Returns:
            bool: True if UTXO was found and marked, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE utxos SET spent = 1 WHERE txid = ? AND vout = ?
        ''', (txid, vout))
        
        conn.commit()
        
        return cursor.rowcount > 0
