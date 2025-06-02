import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
from app.models.utxo_models import TransactionRequest, Input, Output, TransactionResponse

def test_bitcoin_core_builder_minimal():
    """Test BitcoinCoreBuilder with minimal dependencies"""
    builder = BitcoinCoreBuilder()
    
    # Create test request
    request = TransactionRequest(
        inputs=[
            Input(
                txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                vout=0,
                value=5000000,
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
    
    # Mock absolutely everything needed
    with patch('bitcoin.SelectParams') as mock_params, \
         patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTransaction') as mock_tx, \
         patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxIn') as mock_txin, \
         patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxOut') as mock_txout, \
         patch('app.services.transaction.builders.bitcoin_core_builder.b2x') as mock_b2x, \
         patch('bitcoin.wallet.CBitcoinAddress', create=True) as mock_addr:
        
        # Setup CMutableTransaction mock
        tx_instance = MagicMock()
        tx_instance.vin = [MagicMock()]
        tx_instance.vout = [MagicMock()]
        tx_instance.serialize.return_value = b'serialized_tx'
        tx_instance.GetTxid.return_value = b'txid1234'
        mock_tx.return_value = tx_instance
        
        # Setup b2x mock
        mock_b2x.side_effect = lambda x: x.hex() if isinstance(x, bytes) else "mock_hex"
        
        # Setup CBitcoinAddress mock
        addr_mock = MagicMock()
        addr_mock.to_scriptPubKey.return_value = b'script_pubkey'
        mock_addr.return_value = addr_mock
        
        # Call the method under test
        result = builder.build(request, network="testnet")
        
        # Verify result
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        # Assertions
        assert isinstance(result, TransactionResponse)
        assert result.raw_transaction is not None
        assert result.txid is not None
        assert result.fee is not None
        
        # Verify mocks
        mock_params.assert_called_once_with('testnet')
        mock_txin.assert_called_once()
        mock_txout.assert_called_once()

if __name__ == "__main__":
    test_bitcoin_core_builder_minimal()
