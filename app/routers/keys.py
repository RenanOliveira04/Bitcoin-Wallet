from fastapi import APIRouter, HTTPException
from app.models.key_models import KeyRequest, KeyResponse
from app.services.key_service import generate_keys

router = APIRouter()

@router.post("/", response_model=KeyResponse)
def create_keys(request: KeyRequest):
    try:
        return generate_keys(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))