from pydantic import BaseModel

class FeeEstimateModel(BaseModel):
    high: float
    medium: float
    low: float
    min: float
    timestamp: int
    unit: str
