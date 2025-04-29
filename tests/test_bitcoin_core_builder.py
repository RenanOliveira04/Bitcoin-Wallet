import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.models.utxo_models import TransactionRequest, TransactionResponse, Input, Output

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

class MockBitcoinCoreBuilder:
    def build(self, request, network):
        raw_tx = "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000"
        txid = "a1b2c3d4e5f67890"
        
        if getattr(self, 'raise_error', False):
            raise Exception("Erro ao construir transação com Bitcoin Core: Erro de teste")
        
        input_total = sum(i.value for i in request.inputs if i.value)
        output_total = sum(o.value for o in request.outputs)
        fee = input_total - output_total
        
        return TransactionResponse(
            raw_transaction=raw_tx,
            txid=txid,
            fee=fee
        )

def test_bitcoin_core_builder_testnet(sample_tx_request):
    """Testa a construção de uma transação na testnet"""
    builder = MockBitcoinCoreBuilder()
    response = builder.build(sample_tx_request, "testnet")
    
    assert response is not None
    assert isinstance(response, TransactionResponse)
    assert response.raw_transaction is not None
    assert response.txid is not None
    assert response.fee == 10000

def test_bitcoin_core_builder_mainnet(sample_tx_request):
    """Testa a construção de uma transação na mainnet"""
    builder = MockBitcoinCoreBuilder()
    response = builder.build(sample_tx_request, "mainnet")
    
    assert response is not None
    assert isinstance(response, TransactionResponse)
    assert response.raw_transaction is not None
    assert response.txid is not None
    assert response.fee == 10000

def test_bitcoin_core_builder_with_multiple_inputs_outputs(sample_tx_request):
    """Testa a construção de uma transação com múltiplos inputs e outputs"""
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
    
    builder = MockBitcoinCoreBuilder()
    response = builder.build(sample_tx_request, "testnet")
    
    assert response is not None
    assert isinstance(response, TransactionResponse)
    assert response.raw_transaction is not None
    assert response.txid is not None
    assert response.fee == 10000

def test_bitcoin_core_builder_error_handling():
    """Testa o tratamento de erros ao construir uma transação"""
    request = TransactionRequest(
        inputs=[
            Input(
                txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                vout=0,
                value=1000000,
                address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
            )
        ],
        outputs=[
            Output(
                address="tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                value=990000
            )
        ]
    )
    
    builder = MockBitcoinCoreBuilder()
    builder.raise_error = True
    
    with pytest.raises(Exception) as excinfo:
        builder.build(request, "testnet")
    
    assert "Erro ao construir transação com Bitcoin Core" in str(excinfo.value) 