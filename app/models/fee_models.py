from pydantic import BaseModel, Field

class FeeEstimateModel(BaseModel):
    high: float = Field(..., description="Taxa alta para confirmação rápida (~10-20 minutos)")
    medium: float = Field(..., description="Taxa média para confirmação em tempo moderado (~1-3 blocos)")
    low: float = Field(..., description="Taxa baixa para confirmação não urgente (~6+ blocos)")
    min: float = Field(..., description="Taxa mínima aceitável pela rede")
    timestamp: int = Field(..., description="Timestamp Unix da estimativa")
    unit: str = Field(..., description="Unidade da taxa (geralmente sat/vB)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "high": 25.7,
                    "medium": 15.2,
                    "low": 8.9,
                    "min": 1.1,
                    "timestamp": 1650123456,
                    "unit": "sat/vB"
                }
            ]
        }
    }