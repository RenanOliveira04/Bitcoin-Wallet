from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from .models import Base, Wallet, Transaction, UTXO
from ..config import DATABASE_URL
from typing import List, Optional, Dict, Any, Generator
import logging

logger = logging.getLogger(__name__)

# Cria o engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão de banco de dados para uso em operações"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class WalletDBService:
    """Serviço para operações de banco de dados relacionadas às carteiras"""
    
    @staticmethod
    def create_wallet(db: Session, wallet_data: Dict[str, Any]) -> Wallet:
        """Cria uma nova carteira no banco de dados"""
        try:
            wallet = Wallet(
                name=wallet_data.get("name", f"Wallet-{wallet_data['address'][:8]}"),
                address=wallet_data["address"],
                private_key=wallet_data.get("private_key"),  # Save private key
                public_key=wallet_data["public_key"],
                format=wallet_data["format"],
                network=wallet_data["network"],
                derivation_path=wallet_data.get("derivation_path"),
                mnemonic=wallet_data.get("mnemonic")
            )
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            logger.info(f"Carteira criada: {wallet.address}")
            return wallet
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao criar carteira: {e}")
            raise
    
    @staticmethod
    def get_wallet_by_address(db: Session, address: str) -> Optional[Wallet]:
        """Busca uma carteira pelo endereço"""
        return db.query(Wallet).filter(Wallet.address == address).first()
    
    @staticmethod
    def get_all_wallets(db: Session) -> List[Wallet]:
        """Retorna todas as carteiras cadastradas"""
        return db.query(Wallet).all()
    
    @staticmethod
    def delete_wallet(db: Session, address: str) -> bool:
        """Remove uma carteira pelo endereço"""
        wallet = WalletDBService.get_wallet_by_address(db, address)
        if wallet:
            db.delete(wallet)
            db.commit()
            logger.info(f"Carteira removida: {address}")
            return True
        return False

class TransactionDBService:
    """Serviço para operações de banco de dados relacionadas às transações"""
    
    @staticmethod
    def create_transaction(db: Session, transaction_data: Dict[str, Any]) -> Transaction:
        """Registra uma nova transação no banco de dados"""
        try:
            transaction = Transaction(
                wallet_id=transaction_data["wallet_id"],
                txid=transaction_data["txid"],
                amount=transaction_data["amount"],
                fee=transaction_data.get("fee", 0),
                type=transaction_data["type"],
                status=transaction_data.get("status", "pending")
            )
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            logger.info(f"Transação registrada: {transaction.txid}")
            return transaction
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao registrar transação: {e}")
            raise
    
    @staticmethod
    def get_transactions_by_wallet(db: Session, wallet_id: int) -> List[Transaction]:
        """Busca todas as transações de uma carteira"""
        return db.query(Transaction).filter(Transaction.wallet_id == wallet_id).order_by(Transaction.timestamp.desc()).all()
    
    @staticmethod
    def update_transaction_status(db: Session, txid: str, status: str) -> bool:
        """Atualiza o status de uma transação"""
        try:
            transaction = db.query(Transaction).filter(Transaction.txid == txid).first()
            if transaction:
                transaction.status = status
                db.commit()
                logger.info(f"Status da transação atualizado: {txid} -> {status}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao atualizar status da transação: {e}")
            raise

class UTXODBService:
    """Serviço para operações de banco de dados relacionadas aos UTXOs"""
    
    @staticmethod
    def save_utxos(db: Session, wallet_id: int, utxos: List[Dict[str, Any]]) -> List[UTXO]:
        """Salva os UTXOs de uma carteira"""
        try:
            db.query(UTXO).filter(UTXO.wallet_id == wallet_id).delete()
            
            db_utxos = []
            for utxo_data in utxos:
                utxo = UTXO(
                    wallet_id=wallet_id,
                    txid=utxo_data["txid"],
                    vout=utxo_data["vout"],
                    amount=utxo_data["amount"],
                    script_pubkey=utxo_data["script_pubkey"],
                    confirmations=utxo_data.get("confirmations", 0),
                    spendable=utxo_data.get("spendable", True)
                )
                db.add(utxo)
                db_utxos.append(utxo)
            
            db.commit()
            logger.info(f"UTXOs atualizados para wallet_id: {wallet_id}")
            return db_utxos
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar UTXOs: {e}")
            raise
    
    @staticmethod
    def get_utxos_by_wallet(db: Session, wallet_id: int) -> List[UTXO]:
        """Busca todos os UTXOs de uma carteira"""
        return db.query(UTXO).filter(UTXO.wallet_id == wallet_id).all()
    
    @staticmethod
    def mark_utxo_spent(db: Session, txid: str, vout: int) -> bool:
        """Marca um UTXO como gasto"""
        try:
            utxo = db.query(UTXO).filter(UTXO.txid == txid, UTXO.vout == vout).first()
            if utxo:
                utxo.spendable = False
                db.commit()
                logger.info(f"UTXO marcado como gasto: {txid}:{vout}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao marcar UTXO como gasto: {e}")
            raise
