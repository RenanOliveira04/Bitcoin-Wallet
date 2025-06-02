import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sqlite3

sys.path.append(str(Path(__file__).parent.parent))

from app.services.wallet_storage import WalletStorage
from app.models.wallet_models import WalletCreate, WalletResponse, TransactionRecord, UTXORecord


class TestSQLiteStorage:
    """Testes para o armazenamento de carteiras com SQLite"""
    
    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Fixture para criar um arquivo de banco de dados temporário"""
        db_file = tmp_path / "test_wallet.db"
        return str(db_file)
    
    @pytest.fixture
    def wallet_storage(self, temp_db_path):
        """Fixture para criar uma instância de WalletStorage com banco de dados de teste"""
        with patch('app.services.wallet_storage.get_db_path') as mock_db_path:
            mock_db_path.return_value = temp_db_path
            storage = WalletStorage()
            storage.initialize_db()
            yield storage
    
    @pytest.fixture
    def sample_wallet(self):
        """Fixture para criar uma carteira de exemplo"""
        return WalletCreate(
            address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc",
            public_key="0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
            private_key_encrypted="encrypted_key_data",
            format="p2pkh",
            network="testnet",
            name="Test Wallet"
        )
    
    @pytest.fixture
    def sample_transaction(self):
        """Fixture para criar uma transação de exemplo"""
        return TransactionRecord(
            txid="a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
            wallet_address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc",
            amount=50000,
            fee=1000,
            confirmations=3,
            block_height=700000,
            timestamp=1635000000,
            type="send"
        )
    
    @pytest.fixture
    def sample_utxo(self):
        """Fixture para criar um UTXO de exemplo"""
        return UTXORecord(
            txid="a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
            vout=0,
            amount=50000,
            script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
            wallet_address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc",
            confirmations=3
        )
    
    def test_database_initialization(self, temp_db_path):
        """Testa se o banco de dados é inicializado corretamente"""
        with patch('app.services.wallet_storage.get_db_path') as mock_db_path:
            mock_db_path.return_value = temp_db_path
            storage = WalletStorage()
            storage.initialize_db()
            
            assert os.path.exists(temp_db_path)
            
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            assert "wallets" in tables
            assert "transactions" in tables
            assert "utxos" in tables
            
            conn.close()
    
    def test_create_wallet(self, wallet_storage, sample_wallet):
        """Testa a criação de uma carteira no banco de dados"""
        result = wallet_storage.create_wallet(sample_wallet)
        
        assert result.address == sample_wallet.address
        assert result.public_key == sample_wallet.public_key
        assert result.format == sample_wallet.format
        assert result.network == sample_wallet.network
        assert result.name == sample_wallet.name
        
        wallets = wallet_storage.get_all_wallets()
        assert len(wallets) == 1
        assert wallets[0].address == sample_wallet.address
    
    def test_get_wallet_by_address(self, wallet_storage, sample_wallet):
        """Testa a recuperação de uma carteira pelo endereço"""
        wallet_storage.create_wallet(sample_wallet)
        
        result = wallet_storage.get_wallet(sample_wallet.address)
        
        assert result is not None
        assert result.address == sample_wallet.address
        assert result.public_key == sample_wallet.public_key
    
    def test_get_nonexistent_wallet(self, wallet_storage):
        """Testa a tentativa de recuperar uma carteira que não existe"""
        result = wallet_storage.get_wallet("nonexistent_address")
        assert result is None
    
    def test_update_wallet(self, wallet_storage, sample_wallet):
        """Testa a atualização de dados de uma carteira"""
        wallet_storage.create_wallet(sample_wallet)
        
        updated_wallet = WalletCreate(
            address=sample_wallet.address,
            public_key=sample_wallet.public_key,
            private_key_encrypted=sample_wallet.private_key_encrypted,
            format=sample_wallet.format,
            network=sample_wallet.network,
            name="Updated Wallet Name"
        )
        
        result = wallet_storage.update_wallet(sample_wallet.address, updated_wallet)
        
        assert result is not None
        assert result.address == sample_wallet.address
        assert result.name == "Updated Wallet Name"
        
        stored_wallet = wallet_storage.get_wallet(sample_wallet.address)
        assert stored_wallet.name == "Updated Wallet Name"
    
    def test_delete_wallet(self, wallet_storage, sample_wallet):
        """Testa a remoção de uma carteira"""
        wallet_storage.create_wallet(sample_wallet)
        
        assert wallet_storage.get_wallet(sample_wallet.address) is not None
        
        wallet_storage.delete_wallet(sample_wallet.address)
        
        assert wallet_storage.get_wallet(sample_wallet.address) is None
    
    def test_add_transaction(self, wallet_storage, sample_wallet, sample_transaction):
        """Testa a adição de uma transação para uma carteira"""
        wallet_storage.create_wallet(sample_wallet)
        
        result = wallet_storage.add_transaction(sample_transaction)
        
        assert result is not None
        assert result.txid == sample_transaction.txid
        assert result.wallet_address == sample_transaction.wallet_address
        
        transactions = wallet_storage.get_wallet_transactions(sample_wallet.address)
        assert len(transactions) == 1
        assert transactions[0].txid == sample_transaction.txid
    
    def test_add_utxo(self, wallet_storage, sample_wallet, sample_utxo):
        """Testa a adição de um UTXO para uma carteira"""
        wallet_storage.create_wallet(sample_wallet)
        
        result = wallet_storage.add_utxo(sample_utxo)
        
        assert result is not None
        assert result.txid == sample_utxo.txid
        assert result.vout == sample_utxo.vout
        assert result.wallet_address == sample_utxo.wallet_address
        
        utxos = wallet_storage.get_wallet_utxos(sample_wallet.address)
        assert len(utxos) == 1
        assert utxos[0].txid == sample_utxo.txid
    
    def test_update_transaction_confirmations(self, wallet_storage, sample_wallet, sample_transaction):
        """Testa a atualização de confirmações de uma transação"""
        wallet_storage.create_wallet(sample_wallet)
        wallet_storage.add_transaction(sample_transaction)
        
        wallet_storage.update_transaction_confirmations(sample_transaction.txid, 10)
        
        transactions = wallet_storage.get_wallet_transactions(sample_wallet.address)
        assert transactions[0].confirmations == 10
    
    def test_spend_utxo(self, wallet_storage, sample_wallet, sample_utxo):
        """Testa a marcação de um UTXO como gasto"""
        wallet_storage.create_wallet(sample_wallet)
        wallet_storage.add_utxo(sample_utxo)
        
        wallet_storage.spend_utxo(sample_utxo.txid, sample_utxo.vout)
        
        utxos = wallet_storage.get_wallet_utxos(sample_wallet.address)
        assert len(utxos) == 0
