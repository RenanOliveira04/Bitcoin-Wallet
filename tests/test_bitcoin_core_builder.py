import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.models.utxo_models import TransactionRequest, TransactionResponse, Input, Output

class MockCMutableTransaction:
    def __init__(self, inputs=None, outputs=None):
        self.vin = inputs or []
        self.vout = outputs or []
    
    def GetTxid(self):
        return bytes.fromhex("a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890")
    
    def serialize(self):
        return bytes.fromhex("02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000")

class MockBitcoin:
    @staticmethod
    def SelectParams(network):
        return None

class MockCScript:
    def __init__(self, data=None):
        self.data = data or b''

class MockCMutableTxIn:
    def __init__(self, prevout=None, script=None, nSequence=None):
        self.prevout = prevout
        self.scriptSig = script
        self.nSequence = nSequence

class MockCMutableTxOut:
    def __init__(self, value=0, script=None):
        self.nValue = value
        self.scriptPubKey = script

class MockCBitcoinAddress:
    def __init__(self, addr):
        self.addr = addr
    
    def to_scriptPubKey(self):
        return MockCScript(b'script')

def mock_b2x(data):
    if isinstance(data, bytes) and len(data) > 0 and data[0:4] == bytes.fromhex("a1b2c3d4"):
        return "a1b2c3d4e5f67890"
    else:
        return "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000"

# Configuração dos patches
bitcoin_core_patches = [
    patch('bitcoin', MockBitcoin()),
    patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTransaction', MockCMutableTransaction),
    patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxIn', MockCMutableTxIn),
    patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxOut', MockCMutableTxOut),
    patch('app.services.transaction.builders.bitcoin_core_builder.CScript', MockCScript),
    patch('app.services.transaction.builders.bitcoin_core_builder.b2x', mock_b2x),
    patch('bitcoin.wallet.CBitcoinAddress', MockCBitcoinAddress)
]

@pytest.fixture
def sample_tx_request():
    """Cria uma requisição de transação de exemplo para testes"""
    return TransactionRequest(
        inputs=[
            Input(
                txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                vout=0,
                value=5000000,
                script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
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

def test_bitcoin_core_builder_testnet(sample_tx_request):
    """Testa a construção de uma transação na testnet com o BitcoinCoreBuilder"""
    for patched in bitcoin_core_patches:
        patched.start()
    
    try:
        from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
        
        builder = BitcoinCoreBuilder()
        response = builder.build(sample_tx_request, "testnet")
        
        assert response is not None
        assert isinstance(response, TransactionResponse)
        assert response.raw_transaction == "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000"
        assert response.txid == "a1b2c3d4e5f67890"
        assert response.fee == 10000  
    finally:
        for patched in bitcoin_core_patches:
            patched.stop()

def test_bitcoin_core_builder_mainnet(sample_tx_request):
    """Testa a construção de uma transação na mainnet com o BitcoinCoreBuilder"""
    for patched in bitcoin_core_patches:
        patched.start()
    
    try:
        from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
        
        builder = BitcoinCoreBuilder()
        response = builder.build(sample_tx_request, "mainnet")
        
        assert response is not None
        assert isinstance(response, TransactionResponse)
        assert response.raw_transaction == "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000"
        assert response.txid == "a1b2c3d4e5f67890"
        assert response.fee == 10000 
    finally:
        for patched in bitcoin_core_patches:
            patched.stop()

def test_bitcoin_core_builder_with_multiple_inputs_outputs(sample_tx_request):
    """Testa a construção de uma transação com múltiplos inputs e outputs"""
    for patched in bitcoin_core_patches:
        patched.start()
    
    try:
        from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
        
        sample_tx_request.inputs.append(
            Input(
                txid="8b1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283f",
                vout=1,
                value=3000000,
                script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
            )
        )
        
        sample_tx_request.outputs.append(
            Output(
                address="tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
                value=3000000
            )
        )
        
        builder = BitcoinCoreBuilder()
        response = builder.build(sample_tx_request, "testnet")
        
        assert response is not None
        assert isinstance(response, TransactionResponse)
        assert response.raw_transaction == "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000"
        assert response.txid == "a1b2c3d4e5f67890"
        assert response.fee == 10000  
    finally:
        for patched in bitcoin_core_patches:
            patched.stop()

def test_bitcoin_core_builder_error_handling(sample_tx_request):
    """Testa o tratamento de erros ao construir uma transação"""
    patches = bitcoin_core_patches[:-1]
    for patched in patches:
        patched.start()
    
    try:
        from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
        
        with patch('bitcoin.wallet.CBitcoinAddress', side_effect=ValueError("Erro de teste")):
            builder = BitcoinCoreBuilder()
            
            with pytest.raises(Exception) as excinfo:
                builder.build(sample_tx_request, "testnet")
            
            assert "Erro ao construir transação com Bitcoin Core" in str(excinfo.value)
            assert "Erro de teste" in str(excinfo.value)
    finally:
        for patched in patches:
            patched.stop() 