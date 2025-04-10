from pydantic import BaseModel

class ValidateRequest(BaseModel):
    tx_hex: str
    network: str = None

class ValidateResponse(BaseModel):
    is_valid: bool
    details: dict
    issues: list = None
