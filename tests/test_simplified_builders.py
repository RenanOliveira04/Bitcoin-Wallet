import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))

from app.services.transaction.builders.bitcoin_lib_builder import BitcoinLibBuilder
from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
from app.models.utxo_models import TransactionRequest, Input, Output, TransactionResponse


def test_bitcoinlib_builder():
    """Simple test for the BitcoinLibBuilder"""
    builder = BitcoinLibBuilder()
    
    # Create a simple transaction request
    tx_request = TransactionRequest(
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
    
    # Mock the Transaction class
    with patch('app.services.transaction.builders.bitcoin_lib_builder.Transaction') as mock_tx:
        # Setup the mock
        mock_instance = MagicMock()
        mock_instance.hash = "a1b2c3d4e5f67890a1b2c3d4e5f67890"
        mock_instance.txid = "a1b2c3d4e5f67890a1b2c3d4e5f67890"
        mock_instance.raw_hex.return_value = "0200000001abcdef"
        mock_instance.sign = MagicMock()
        mock_tx.return_value = mock_instance
        
        # Test the builder
        response = builder.build(tx_request, network="testnet")
        
        # Check the response
        assert isinstance(response, TransactionResponse)
        assert response.txid is not None
        assert response.raw_transaction is not None
        assert response.fee is not None


def test_bitcoin_core_builder():
    """Simple test for the BitcoinCoreBuilder"""
    builder = BitcoinCoreBuilder()
    
    # Create a simple transaction request
    tx_request = TransactionRequest(
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
    
    # Mock necessary components
    with patch.object(BitcoinCoreBuilder, 'select_chain_params') as mock_select, \
         patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTransaction') as mock_tx, \
         patch('bitcoin.wallet.CBitcoinAddress') as mock_addr:
        
        # Setup mocks
        mock_tx_instance = MagicMock()
        mock_tx_instance.serialize.return_value = b'0200000001abcdef'
        mock_tx_instance.GetTxid.return_value = b'a1b2c3d4e5f67890'
        mock_tx.return_value = mock_tx_instance
        
        mock_addr_instance = MagicMock()
        mock_addr_instance.to_scriptPubKey.return_value = b'script'
        mock_addr.return_value = mock_addr_instance
        
        # Patch the calculate_tx_fee method
        with patch.object(BitcoinCoreBuilder, 'calculate_tx_fee', return_value=10000):
            # Test the builder
            response = builder.build(tx_request, network="testnet")
            
            # Check the response
            assert isinstance(response, TransactionResponse)
            assert response.txid is not None
            assert response.raw_transaction is not None
            assert response.fee is not None
            
            # Verify mocks were called
            mock_select.assert_called_once_with('testnet')
