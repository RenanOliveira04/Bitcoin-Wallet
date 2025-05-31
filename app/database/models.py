from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import os
from pathlib import Path

Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String, unique=True, index=True)
    public_key = Column(String)
    format = Column(String)  # p2pkh, p2sh, p2wpkh, p2tr
    network = Column(String)  # testnet, mainnet
    derivation_path = Column(String, nullable=True)
    mnemonic = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
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
    data_dir = Path.home() / ".bitcoin-wallet" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = data_dir / "wallet.db"
    return f"sqlite:///{db_path}"

def init_db():
    engine = create_engine(get_database_path())
    Base.metadata.create_all(bind=engine)
    return engine
