import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))

from app.services.transaction.builders.bitcoin_lib_builder import BitcoinLibBuilder
from app.services.transaction.builders.bitcoin_core_builder import BitcoinCoreBuilder
from app.models.utxo_models import TransactionRequest, Input, Output


class TestTransactionBuilders:
    """Testes para os diferentes builders de transação"""
    
    @pytest.fixture
    def sample_tx_request(self):
        """Cria uma requisição de transação para testes"""
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

    def test_bitcoinlib_builder(self, sample_tx_request):
        """Testa o builder de transações baseado em bitcoinlib"""
        builder = BitcoinLibBuilder()
        
        with patch('app.services.transaction.builders.bitcoin_lib_builder.Input') as mock_input, \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Output') as mock_output, \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Transaction') as mock_tx:
            
            mock_tx_instance = MagicMock()
            mock_tx_instance.hash = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.txid = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.sign = MagicMock()
            mock_tx_instance.raw_hex = MagicMock(return_value="020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff")
            mock_tx_instance.input_total = 5000000
            mock_tx_instance.output_total = 4990000
            
            mock_tx.return_value = mock_tx_instance
            
            result = builder.build(sample_tx_request, network="testnet")
            
            assert result is not None
            assert "raw_transaction" in result.model_dump()
            assert "txid" in result.model_dump()
            assert "fee" in result.model_dump()
            
            mock_input.assert_called_once()
            mock_output.assert_called_once()

    def test_bitcoin_core_builder(self, sample_tx_request):
        """Testa o builder de transações baseado em python-bitcoinlib (Bitcoin Core)"""
        builder = BitcoinCoreBuilder()
        
        with patch.object(BitcoinCoreBuilder, 'select_chain_params') as mock_select_chain, \
             patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTransaction') as mock_tx, \
             patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxIn') as mock_tx_in, \
             patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxOut') as mock_tx_out, \
             patch('app.services.transaction.builders.bitcoin_core_builder.CBitcoinAddress') as mock_addr:
            
            # Mock transaction instance
            mock_tx_instance = MagicMock()
            mock_tx_instance.serialize.return_value = bytes.fromhex("020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff")
            mock_tx_instance.GetTxid.return_value = bytes.fromhex("a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890")
            mock_tx_instance.vin = [MagicMock()]
            mock_tx_instance.vout = [MagicMock()]
            mock_tx.return_value = mock_tx_instance
            
            # Mock Bitcoin address script generation
            mock_addr_instance = MagicMock()
            mock_addr_instance.to_scriptPubKey.return_value = b'script'
            mock_addr.return_value = mock_addr_instance
            
            # Set up input and output mocks
            mock_tx_in_instance = MagicMock()
            mock_tx_in.return_value = mock_tx_in_instance
            
            mock_tx_out_instance = MagicMock()
            mock_tx_out.return_value = mock_tx_out_instance
            
            # Calculate fee mock
            with patch.object(BitcoinCoreBuilder, 'calculate_tx_fee', return_value=10000):
                result = builder.build(sample_tx_request, network="testnet")
                
                assert result is not None
                assert "raw_transaction" in result.model_dump()
                assert "txid" in result.model_dump()
                assert "fee" in result.model_dump()
                
                mock_tx_in.assert_called_once()
                mock_tx_out.assert_called()
                mock_select_chain.assert_called_once_with('testnet')

    def test_builders_with_multiple_inputs_outputs(self):
        """Testa os builders com múltiplos inputs e outputs"""
        tx_request = TransactionRequest(
            inputs=[
                Input(
                    txid="7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    vout=0,
                    value=5000000,
                    script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
                ),
                Input(
                    txid="8b1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283f",
                    vout=1,
                    value=3000000,
                    script="76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    address="mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
                )
            ],
            outputs=[
                Output(
                    address="tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    value=4000000
                ),
                Output(
                    address="tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
                    value=3900000
                )
            ],
            fee_rate=2.0
        )
        
        lib_builder = BitcoinLibBuilder()
        with patch('app.services.transaction.builders.bitcoin_lib_builder.Input'), \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Output'), \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Transaction') as mock_tx:
            
            mock_tx_instance = MagicMock()
            mock_tx_instance.hash = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.txid = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.sign = MagicMock()
            mock_tx_instance.raw_hex = MagicMock(return_value="020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff")
            mock_tx_instance.input_total = 8000000
            mock_tx_instance.output_total = 7900000
            
            mock_tx.return_value = mock_tx_instance
            
            result = lib_builder.build(tx_request, network="testnet")
            assert result is not None
        
        core_builder = BitcoinCoreBuilder()
        with patch.object(BitcoinCoreBuilder, 'select_chain_params'), \
             patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTransaction') as mock_tx, \
             patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxIn'), \
             patch('app.services.transaction.builders.bitcoin_core_builder.CMutableTxOut'), \
             patch('app.services.transaction.builders.bitcoin_core_builder.CBitcoinAddress') as mock_addr:
            
            # Mock transaction instance
            mock_tx_instance = MagicMock()
            mock_tx_instance.serialize.return_value = bytes.fromhex("020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff")
            mock_tx_instance.GetTxid.return_value = bytes.fromhex("a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890")
            mock_tx_instance.vin = [MagicMock(), MagicMock()]
            mock_tx_instance.vout = [MagicMock(), MagicMock()]
            mock_tx.return_value = mock_tx_instance
            
            # Mock Bitcoin address script generation
            mock_addr_instance = MagicMock()
            mock_addr_instance.to_scriptPubKey.return_value = b'script'
            mock_addr.return_value = mock_addr_instance
            
            # Calculate fee mock
            with patch.object(BitcoinCoreBuilder, 'calculate_tx_fee', return_value=100000):
                result = core_builder.build(tx_request, network="testnet")
                assert result is not None
                assert result.raw_transaction is not None
                assert result.txid is not None
                assert result.fee == 100000

    def test_fee_calculation(self, sample_tx_request):
        """Testa o cálculo correto de taxas"""
        lib_builder = BitcoinLibBuilder()
        
        with patch('app.services.transaction.builders.bitcoin_lib_builder.Input'), \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Output'), \
             patch('app.services.transaction.builders.bitcoin_lib_builder.Transaction') as mock_tx:
            
            mock_tx_instance = MagicMock()
            mock_tx_instance.hash = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.txid = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
            mock_tx_instance.sign = MagicMock()
            mock_tx_instance.raw_hex = MagicMock(return_value="020000000001010000000000000000000000000000000000000000000000000000000000000000ffffffff")
            mock_tx_instance.input_total = 5000000
            mock_tx_instance.output_total = 4990000
            
            mock_tx.return_value = mock_tx_instance
            
            result = lib_builder.build(sample_tx_request, network="testnet")
            
            assert result.fee == 10000
