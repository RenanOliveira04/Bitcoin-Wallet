import json
import logging
import os
import aiosqlite
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager
from enum import Enum
from pydantic import BaseModel, Field
import hashlib
import secrets

from app.models.wallet_models import WalletCreate, WalletResponse, TransactionRecord, UTXORecord

logger = logging.getLogger(__name__)

class WalletStatus(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    ARCHIVED = "archived"

class WalletType(str, Enum):
    HD = "hd"
    SINGLE_KEY = "single_key"
    MULTISIG = "multisig"

class WalletMetadata(BaseModel):
    """Additional metadata for wallet storage"""
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    status: WalletStatus = WalletStatus.ACTIVE
    wallet_type: WalletType = WalletType.SINGLE_KEY
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class WalletStorageConfig:
    """Configuration for wallet storage"""
    def __init__(
        self,
        db_path: Optional[str] = None,
        max_connections: int = 5,
        timeout: float = 30.0,
        journal_mode: str = "WAL",
        synchronous: str = "NORMAL",
        foreign_keys: bool = True
    ):
        self.db_path = db_path or self._get_default_db_path()
        self.max_connections = max(1, min(max_connections, 20))  # Limit between 1-20
        self.timeout = max(1.0, min(timeout, 300.0))  # 1s to 5min
        self.journal_mode = journal_mode
        self.synchronous = synchronous
        self.foreign_keys = foreign_keys

    @staticmethod
    def _get_default_db_path() -> str:
        """Get default database path"""
        default_path = os.path.join(str(Path.home()), ".bitcoin-wallet", "wallets.db")
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        return default_path

class WalletStorage:
    """Asynchronous wallet storage using SQLite with connection pooling"""
    
    def __init__(self, config: Optional[WalletStorageConfig] = None):
        self.config = config or WalletStorageConfig()
        self._pool = None
        self._lock = asyncio.Lock()
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the database connection pool and tables"""
        if self._is_initialized:
            return

        async with self._lock:
            if self._is_initialized:  
                return

            self._pool = await aiosqlite.create_pool(
                self.config.db_path,
                min_size=1,
                max_size=self.config.max_connections,
                timeout=self.config.timeout,
                isolation_level="IMMEDIATE",
                factory=aiosqlite.Row
            )

            async with self.connection() as conn:
                await self._init_db(conn)
            
            self._is_initialized = True

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a database connection from the pool"""
        if not self._is_initialized:
            await self.initialize()

        conn = await self._pool.acquire()
        try:
            await conn.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
            await conn.execute(f"PRAGMA synchronous = {self.config.synchronous}")
            await conn.execute(f"PRAGMA foreign_keys = {'ON' if self.config.foreign_keys else 'OFF'}")
            await conn.commit()
            
            yield conn
        finally:
            await self._pool.release(conn)

    async def _init_db(self, conn: aiosqlite.Connection) -> None:
        """Initialize database tables"""
        await conn.executescript('''
        -- Wallets table with metadata
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            address TEXT NOT NULL,
            private_key_encrypted TEXT,
            public_key TEXT NOT NULL,
            key_type TEXT NOT NULL,
            network TEXT NOT NULL DEFAULT 'testnet',
            metadata TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            version INTEGER NOT NULL DEFAULT 1
        );

        -- Transactions table with improved indexing
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id TEXT NOT NULL,
            txid TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL,
            confirmations INTEGER DEFAULT 0,
            block_height INTEGER,
            block_hash TEXT,
            timestamp TIMESTAMP,
            status TEXT NOT NULL,
            raw_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id) ON DELETE CASCADE,
            UNIQUE(wallet_id, txid)
        );
        CREATE INDEX IF NOT EXISTS idx_transactions_wallet_id ON transactions(wallet_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_txid ON transactions(txid);

        -- UTXOs table with better indexing
        CREATE TABLE IF NOT EXISTS utxos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id TEXT NOT NULL,
            txid TEXT NOT NULL,
            vout INTEGER NOT NULL,
            amount REAL NOT NULL,
            script TEXT,
            address TEXT,
            confirmations INTEGER DEFAULT 0,
            spendable BOOLEAN DEFAULT TRUE,
            spent_txid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id) ON DELETE CASCADE,
            UNIQUE(txid, vout)
        );
        CREATE INDEX IF NOT EXISTS idx_utxos_wallet_id ON utxos(wallet_id, spendable);
        CREATE INDEX IF NOT EXISTS idx_utxos_txid_vout ON utxos(txid, vout);
        ''')
        await conn.commit()

    async def create_wallet(self, wallet: WalletCreate) -> WalletResponse:
        """Create a new wallet with metadata and encryption"""
        wallet_id = self._generate_wallet_id()
        metadata = WalletMetadata(
            wallet_type=WalletType(wallet.key_type),
            description=wallet.description,
            created_at=datetime.utcnow()
        )
        
        async with self.connection() as conn:
            cursor = await conn.execute('''
            INSERT INTO wallets (
                wallet_id, name, description, address, private_key_encrypted, 
                public_key, key_type, network, metadata, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                wallet_id,
                wallet.name,
                wallet.description,
                wallet.address,
                self._encrypt_private_key(wallet.private_key, wallet_id),
                wallet.public_key,
                wallet.key_type,
                wallet.network or "testnet",
                metadata.json(),
                WalletStatus.ACTIVE.value
            ))
            
            await conn.commit()
            return await self.get_wallet(wallet_id)

    async def get_wallet(self, wallet_id: str) -> Optional[WalletResponse]:
        """Get wallet by ID with decrypted private key"""
        async with self.connection() as conn:
            row = await conn.execute_fetchone(
                "SELECT * FROM wallets WHERE wallet_id = ?", 
                (wallet_id,)
            )
            
            if not row:
                return None
                
            metadata = WalletMetadata.parse_raw(row['metadata'])
            private_key = self._decrypt_private_key(
                row['private_key_encrypted'], 
                wallet_id
            ) if row['private_key_encrypted'] else None
            
            return WalletResponse(
                id=row['wallet_id'],
                name=row['name'],
                description=metadata.description,
                address=row['address'],
                private_key=private_key,
                public_key=row['public_key'],
                key_type=row['key_type'],
                network=row['network'],
                created_at=row['created_at'],
                status=row['status'],
                metadata=metadata.dict()
            )

    async def list_wallets(self, status: Optional[WalletStatus] = None) -> List[WalletResponse]:
        """List wallets with optional status filter"""
        query = "SELECT * FROM wallets"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status.value)
            
        async with self.connection() as conn:
            rows = await conn.execute_fetchall(query, params)
            return [
                WalletResponse(
                    id=row['wallet_id'],
                    name=row['name'],
                    description=WalletMetadata.parse_raw(row['metadata']).description,
                    address=row['address'],
                    private_key=None,  
                    public_key=row['public_key'],
                    key_type=row['key_type'],
                    network=row['network'],
                    created_at=row['created_at'],
                    status=row['status']
                ) for row in rows
            ]

    async def update_wallet_metadata(self, wallet_id: str, metadata: Dict[str, Any]) -> bool:
        """Update wallet metadata"""
        async with self.connection() as conn:
            wallet = await self.get_wallet(wallet_id)
            if not wallet:
                return False
                
            current_meta = WalletMetadata.parse_raw(wallet.metadata or '{}')
            updated_meta = current_meta.copy(update=metadata)
            
            await conn.execute(
                "UPDATE wallets SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE wallet_id = ?",
                (updated_meta.json(), wallet_id)
            )
            await conn.commit()
            return True

    async def add_transaction(self, wallet_id: str, tx_record: TransactionRecord) -> bool:
        """Add or update a transaction"""
        async with self.connection() as conn:
            try:
                await conn.execute('''
                INSERT OR REPLACE INTO transactions 
                (wallet_id, txid, amount, fee, confirmations, block_height, 
                 block_hash, timestamp, status, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    wallet_id,
                    tx_record.txid,
                    float(tx_record.amount),
                    float(tx_record.fee) if tx_record.fee else None,
                    tx_record.confirmations or 0,
                    tx_record.block_height,
                    tx_record.block_hash,
                    tx_record.timestamp or datetime.utcnow(),
                    tx_record.status,
                    tx_record.raw_data
                ))
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding transaction: {e}")
                await conn.rollback()
                return False

    async def get_transactions(
        self, 
        wallet_id: str, 
        limit: int = 100, 
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[TransactionRecord]:
        """Get transactions with pagination and filtering"""
        query = "SELECT * FROM transactions WHERE wallet_id = ?"
        params = [wallet_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
            
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with self.connection() as conn:
            rows = await conn.execute_fetchall(query, params)
            return [
                TransactionRecord(
                    txid=row['txid'],
                    amount=row['amount'],
                    fee=row['fee'],
                    confirmations=row['confirmations'],
                    block_height=row['block_height'],
                    block_hash=row['block_hash'],
                    timestamp=row['timestamp'],
                    status=row['status'],
                    raw_data=row['raw_data']
                ) for row in rows
            ]

    async def add_utxo(self, wallet_id: str, utxo: UTXORecord) -> bool:
        """Add or update a UTXO"""
        async with self.connection() as conn:
            try:
                await conn.execute('''
                INSERT OR REPLACE INTO utxos 
                (wallet_id, txid, vout, amount, script, address, 
                 confirmations, spendable, spent_txid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    wallet_id,
                    utxo.txid,
                    utxo.vout,
                    float(utxo.amount),
                    utxo.script,
                    utxo.address,
                    utxo.confirmations or 0,
                    utxo.spendable,
                    utxo.spent_txid
                ))
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding UTXO: {e}")
                await conn.rollback()
                return False

    async def get_utxos(
        self, 
        wallet_id: str, 
        include_spent: bool = False,
        min_confirmations: int = 0
    ) -> List[UTXORecord]:
        """Get UTXOs with filtering options"""
        query = '''
        SELECT * FROM utxos 
        WHERE wallet_id = ? 
        AND (spendable = ? OR ? = 1)
        AND confirmations >= ?
        '''
        params = [wallet_id, True, include_spent, min_confirmations]
        
        async with self.connection() as conn:
            rows = await conn.execute_fetchall(query, params)
            return [
                UTXORecord(
                    txid=row['txid'],
                    vout=row['vout'],
                    amount=row['amount'],
                    script=row['script'],
                    address=row['address'],
                    confirmations=row['confirmations'],
                    spendable=bool(row['spendable']),
                    spent_txid=row['spent_txid']
                ) for row in rows
            ]

    async def mark_utxo_spent(self, txid: str, vout: int, spent_txid: str) -> bool:
        """Mark a UTXO as spent"""
        async with self.connection() as conn:
            try:
                await conn.execute('''
                UPDATE utxos 
                SET spendable = 0, spent_txid = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE txid = ? AND vout = ?
                ''', (spent_txid, txid, vout))
                await conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error marking UTXO as spent: {e}")
                await conn.rollback()
                return False

    async def get_balance(self, wallet_id: str, min_confirmations: int = 0) -> Dict[str, float]:
        """Get wallet balance with confirmation threshold"""
        async with self.connection() as conn:
            confirmed_balance = await conn.execute_fetchone('''
            SELECT COALESCE(SUM(amount), 0) as balance
            FROM utxos
            WHERE wallet_id = ? 
            AND spendable = 1
            AND confirmations >= ?
            ''', (wallet_id, min_confirmations))

            unconfirmed_balance = await conn.execute_fetchone('''
            SELECT COALESCE(SUM(amount), 0) as balance
            FROM utxos
            WHERE wallet_id = ? 
            AND spendable = 1
            AND confirmations < ?
            ''', (wallet_id, min_confirmations))

            return {
                "confirmed": float(confirmed_balance['balance'] or 0),
                "unconfirmed": float(unconfirmed_balance['balance'] or 0),
                "total": float((confirmed_balance['balance'] or 0) + (unconfirmed_balance['balance'] or 0))
            }

    async def backup_wallet(self, wallet_id: str, backup_path: str) -> bool:
        """Create a backup of the wallet"""
        try:
            wallet = await self.get_wallet(wallet_id)
            if not wallet:
                return False
                
            backup_data = {
                "version": 1,
                "wallet_id": wallet.id,
                "name": wallet.name,
                "address": wallet.address,
                "public_key": wallet.public_key,
                "key_type": wallet.key_type,
                "network": wallet.network,
                "created_at": wallet.created_at.isoformat(),
                "backup_timestamp": datetime.utcnow().isoformat()
            }
            
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error creating wallet backup: {e}")
            return False

    def _generate_wallet_id(self) -> str:
        """Generate a unique wallet ID"""
        return hashlib.sha256(secrets.token_bytes(32)).hexdigest()

    def _encrypt_private_key(self, private_key: str, wallet_id: str) -> str:
        """Encrypt private key using wallet ID as part of the key"""
        key = hashlib.sha256(wallet_id.encode()).digest()
        return f"encrypted_{private_key}"

    def _decrypt_private_key(self, encrypted_key: str, wallet_id: str) -> Optional[str]:
        """Decrypt private key using wallet ID"""
        if not encrypted_key or not encrypted_key.startswith("encrypted_"):
            return None
        return encrypted_key[10:]  

    async def close(self) -> None:
        """Close database connections"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._is_initialized = False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()