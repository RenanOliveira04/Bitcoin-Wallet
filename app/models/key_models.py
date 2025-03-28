from pydantic import BaseModel

class KeyRequest(BaseModel):
    network: str = "testnet"
    password: str | None = None

class KeyResponse(BaseModel):
    private_key: str
    public_key: str
    address: str