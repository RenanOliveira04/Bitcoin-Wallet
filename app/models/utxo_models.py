from pydantic import BaseModel, field_serializer
from typing import List, Optional, Dict, Any, Union

class Input(BaseModel):
    txid: str
    vout: int
    value: Optional[int] = None
    script: Optional[str] = None
    sequence: Optional[int] = None
    address: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                    "vout": 0,
                    "value": 5000000,
                    "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                    "address": "mxosQ4CvQR8ipfWdRktyB3u16tauEdamGc"
                }
            ]
        }
    }
    
    @field_serializer('vout')
    def serialize_vout(self, vout: int) -> Union[int, str]:
        return vout
    
    @field_serializer('value')
    def serialize_value(self, value: Optional[int]) -> Optional[Union[int, str]]:
        if value is None:
            return None
        return value

class Output(BaseModel):
    address: str
    value: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    "value": 4990000
                }
            ]
        }
    }
    
    @field_serializer('value')
    def serialize_value(self, value: int) -> Union[int, str]:
        return value

class TransactionRequest(BaseModel):
    inputs: List[Input]  
    outputs: List[Output] 
    fee_rate: Optional[float] = None 
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "inputs": [
                        {
                            "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                            "vout": 0,
                            "value": 5000000,
                            "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac"
                        }
                    ],
                    "outputs": [
                        {
                            "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                            "value": 4990000
                        }
                    ],
                    "fee_rate": 2.0
                }
            ]
        }
    }
    
    def to_bitcoinlib_format(self) -> Dict[str, Any]:
        formatted_inputs = []
        for input_tx in self.inputs:
            formatted_input = {
                "txid": input_tx.txid,
                "output_n": input_tx.vout,
            }
            if input_tx.script:
                formatted_input["script"] = input_tx.script
            if input_tx.value:
                formatted_input["value"] = input_tx.value
            if input_tx.sequence:
                formatted_input["sequence"] = input_tx.sequence
            formatted_inputs.append(formatted_input)
        
        formatted_outputs = []
        for output in self.outputs:
            formatted_outputs.append({
                "address": output.address,
                "value": output.value
            })
            
        return {
            "inputs": formatted_inputs,
            "outputs": formatted_outputs,
            "fee": self.fee_rate
        }

class TransactionResponse(BaseModel):
    raw_transaction: str
    txid: str
    fee: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "raw_transaction": "02000000013e283d571fe99cb1ebb0c012ec2c8bf785f5a39435de8636e67a65ec80daea17000000006a47304402204b3b868a9a17698b37f17c35d58a6383ec5226a8e68b39d90648b9cfd46633bf02204cff73c675f01a2ea7bf6bf80440f3f0e1bbb91e3c95064493b0ccc8a97c1352012103a13a20be306339d11e88a324ea96851ce728ba85548e8ff6f2386f9466e2ca8dffffffff0150c30000000000001976a914d0c59903c5bac2868760e90fd521a4665aa7652088ac00000000",
                    "txid": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
                    "fee": 10000
                }
            ]
        }
    }

class UTXOResponse(BaseModel):
    address: str
    utxos: List[Input]
    total_utxos: int
    total_amount: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                    "utxos": [
                        {
                            "txid": "7a1ae0dc85ea676e63485de4394a5d78fbfc8c02e012c0ebb19ce91f573d283e",
                            "vout": 0,
                            "value": 5000000,
                            "script": "76a914d0c59903c5bac2868760e90fd521a4665aa7652088ac",
                            "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
                        }
                    ],
                    "total_utxos": 1,
                    "total_amount": 5000000
                }
            ]
        }
    }