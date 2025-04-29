import pytest
from unittest.mock import MagicMock, patch
from bitcoin.core import CMutableTransaction
import bitcoin
from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
from app.models.utxo_models import TransactionRequest, Input, Output

@pytest.fixture
def sample_tx_request():
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

@patch('bitcoin.wallet.CBitcoinAddress')
def test_bitcoin_core_builder_testnet(mock_address, sample_tx_request):
    mock_script_pubkey = MagicMock()
    mock_address_instance = MagicMock()
    mock_address_instance.to_scriptPubKey.return_value = mock_script_pubkey
    mock_address.return_value = mock_address_instance
    
    builder = BitcoinCoreBuilder()
    response = builder.build(sample_tx_request, "testnet")
    
    assert response is not None
    assert response.raw_transaction is not None
    assert response.txid is not None
    assert response.fee == 10000 
    
    assert bitcoin.get_current_params().NAME == "testnet"

@patch('bitcoin.wallet.CBitcoinAddress')
def test_bitcoin_core_builder_mainnet(mock_address, sample_tx_request):
    mock_script_pubkey = MagicMock()
    mock_address_instance = MagicMock()
    mock_address_instance.to_scriptPubKey.return_value = mock_script_pubkey
    mock_address.return_value = mock_address_instance
    
    builder = BitcoinCoreBuilder()
    response = builder.build(sample_tx_request, "mainnet")
    
    assert response is not None
    assert response.raw_transaction is not None
    assert response.txid is not None
    assert response.fee == 10000 
    
    assert bitcoin.get_current_params().NAME == "mainnet"

@patch('bitcoin.wallet.CBitcoinAddress')
def test_bitcoin_core_builder_with_multiple_inputs_outputs(mock_address, sample_tx_request):
    mock_script_pubkey = MagicMock()
    mock_address_instance = MagicMock()
    mock_address_instance.to_scriptPubKey.return_value = mock_script_pubkey
    mock_address.return_value = mock_address_instance
    
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
    assert response.raw_transaction is not None
    assert response.txid is not None
    assert response.fee == 10000  
    
    tx_bytes = bytes.fromhex(response.raw_transaction)
    tx = CMutableTransaction.deserialize(tx_bytes)
    assert len(tx.vin) == 2
    assert len(tx.vout) == 2

@patch('bitcoin.wallet.CBitcoinAddress')
def test_bitcoin_core_builder_error_handling(mock_address, sample_tx_request):
    mock_address.side_effect = ValueError("Erro de teste")
    
    builder = BitcoinCoreBuilder()
    
    with pytest.raises(Exception) as excinfo:
        builder.build(sample_tx_request, "testnet")
    
    assert "Erro ao construir transação com Bitcoin Core" in str(excinfo.value) 