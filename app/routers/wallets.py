from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.service import get_db, WalletDBService, TransactionDBService, UTXODBService
from app.database.models import Wallet, Transaction, UTXO
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

router = APIRouter()

class WalletFormat(str, Enum):
    p2pkh = "p2pkh"
    p2sh = "p2sh"
    p2wpkh = "p2wpkh"
    p2tr = "p2tr"

class Network(str, Enum):
    testnet = "testnet"
    mainnet = "mainnet"

class WalletCreate(BaseModel):
    name: str = Field(None, description="Nome da carteira")
    address: str = Field(..., description="Endereço Bitcoin")
    private_key: Optional[str] = Field(None, description="Chave privada em formato WIF")
    public_key: str = Field(..., description="Chave pública em formato hexadecimal")
    format: WalletFormat = Field(..., description="Formato do endereço")
    network: Network = Field(..., description="Rede Bitcoin")
    key_generation_method: str = Field("entropy", description="Método de geração da chave (entropy, bip39, bip32)")
    derivation_path: Optional[str] = Field(None, description="Caminho de derivação BIP32")
    mnemonic: Optional[str] = Field(None, description="Frase mnemônica")

class WalletResponse(BaseModel):
    id: int = Field(..., description="ID da carteira")
    name: str = Field(..., description="Nome da carteira")
    address: str = Field(..., description="Endereço Bitcoin")
    private_key: Optional[str] = Field(None, description="Chave privada em formato WIF")
    public_key: str = Field(..., description="Chave pública")
    format: str = Field(..., description="Formato do endereço")
    network: str = Field(..., description="Rede Bitcoin")
    key_generation_method: str = Field(..., description="Método de geração da chave (entropy, bip39, bip32)")
    derivation_path: Optional[str] = Field(None, description="Caminho de derivação BIP32")
    mnemonic: Optional[str] = Field(None, description="Frase mnemônica")
    created_at: datetime = Field(..., description="Data de criação")
    
    class Config:
        orm_mode = True

class TransactionResponse(BaseModel):
    id: int = Field(..., description="ID da transação")
    wallet_id: int = Field(..., description="ID da carteira")
    txid: str = Field(..., description="ID da transação na blockchain")
    amount: float = Field(..., description="Valor da transação")
    fee: float = Field(..., description="Taxa da transação")
    type: str = Field(..., description="Tipo (enviar/receber)")
    status: str = Field(..., description="Status da transação")
    timestamp: datetime = Field(..., description="Data e hora")
    
    class Config:
        orm_mode = True

class UTXOResponse(BaseModel):
    id: int = Field(..., description="ID do UTXO")
    wallet_id: int = Field(..., description="ID da carteira")
    txid: str = Field(..., description="ID da transação")
    vout: int = Field(..., description="Índice de saída")
    amount: float = Field(..., description="Valor do UTXO")
    script_pubkey: str = Field(..., description="Script pubkey")
    confirmations: int = Field(..., description="Número de confirmações")
    spendable: bool = Field(..., description="Se o UTXO pode ser gasto")
    
    class Config:
        orm_mode = True

@router.post("/", response_model=WalletResponse, description="Salva uma carteira no armazenamento local")
def create_wallet(wallet: WalletCreate, db: Session = Depends(get_db)):
    existing_wallet = WalletDBService.get_wallet_by_address(db, wallet.address)
    if existing_wallet:
        raise HTTPException(status_code=400, detail="Carteira com este endereço já existe")
    
    return WalletDBService.create_wallet(db, wallet.dict())

@router.get("/", response_model=List[WalletResponse], description="Lista todas as carteiras salvas localmente")
def list_wallets(db: Session = Depends(get_db)):
    return WalletDBService.get_all_wallets(db)

@router.get("/{address}", response_model=WalletResponse, description="Busca uma carteira pelo endereço")
def get_wallet(address: str, db: Session = Depends(get_db)):
    wallet = WalletDBService.get_wallet_by_address(db, address)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    
    wallet_dict = wallet.__dict__.copy()
    
    wallet_dict.pop('_sa_instance_state', None)
    
    if hasattr(wallet, 'private_key') and wallet.private_key:
        wallet_dict['private_key'] = wallet.private_key
    else:
        wallet_dict['private_key'] = None
        
    required_fields = ['id', 'name', 'address', 'public_key', 'format', 'network', 'key_generation_method', 'created_at']
    for field in required_fields:
        if field not in wallet_dict:
            wallet_dict[field] = getattr(wallet, field, None)
    
    return wallet_dict

@router.delete("/{address}", description="Remove uma carteira do armazenamento local")
def delete_wallet(address: str, db: Session = Depends(get_db)):
    if not WalletDBService.delete_wallet(db, address):
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    return {"detail": "Carteira removida com sucesso"}

@router.get("/{address}/transactions", response_model=List[TransactionResponse], description="Lista as transações de uma carteira")
def get_wallet_transactions(address: str, db: Session = Depends(get_db)):
    wallet = WalletDBService.get_wallet_by_address(db, address)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    
    return TransactionDBService.get_transactions_by_wallet(db, wallet.id)

@router.get("/{address}/utxos", response_model=List[UTXOResponse], description="Lista os UTXOs de uma carteira")
def get_wallet_utxos(address: str, db: Session = Depends(get_db)):
    wallet = WalletDBService.get_wallet_by_address(db, address)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Carteira não encontrada")
    
    return UTXODBService.get_utxos_by_wallet(db, wallet.id)