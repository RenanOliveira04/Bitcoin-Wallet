from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional, Dict, Any, Union

class Input(BaseModel):
    txid: str
    vout: int
    script: Optional[str] = None
    value: Optional[int] = None
    sequence: Optional[int] = None
    
    # Serializer para compatibilidade com bitcoinlib
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
    
    # Serializer para compatibilidade com bitcoinlib
    @field_serializer('value')
    def serialize_value(self, value: int) -> Union[int, str]:
        return value

class TransactionRequest(BaseModel):
    inputs: List[Input]  
    outputs: List[Output] 
    fee_rate: Optional[float] = None 
    
    # Método para converter para o formato esperado pela bitcoinlib
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