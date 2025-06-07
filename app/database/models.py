from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
from pathlib import Path
from app.config import DATA_DIR

Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    private_key = Column(String, nullable=True)  # Pode ser nulo para carteiras somente leitura
    public_key = Column(String, nullable=False)
    format = Column(String, nullable=False)  # p2pkh, p2sh, p2wpkh, p2tr
    network = Column(String, nullable=False)  # testnet, mainnet
    key_generation_method = Column(String, default='entropy')  # entropy, bip39, bip32
    derivation_path = Column(String, nullable=True)
    mnemonic = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    transactions = relationship("Transaction", back_populates="wallet")
    utxos = relationship("UTXO", back_populates="wallet")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    txid = Column(String, index=True)
    amount = Column(Float)
    fee = Column(Float)
    type = Column(String)  # send, receive
    status = Column(String)  # pending, confirmed
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    wallet = relationship("Wallet", back_populates="transactions")

class UTXO(Base):
    __tablename__ = "utxos"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    txid = Column(String)
    vout = Column(Integer)
    amount = Column(Float)
    script_pubkey = Column(String)
    confirmations = Column(Integer)
    spendable = Column(Boolean, default=True)
    
    wallet = relationship("Wallet", back_populates="utxos")

def get_database_path():
    """Get the path to the SQLite database file."""
    db_path = Path(DATA_DIR) / 'bitcoin_wallet.db'
    return f"sqlite:///{db_path.absolute().as_posix()}"
