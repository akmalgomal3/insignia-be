from fastapi import APIRouter, Depends
from app.core.security import verify_token

router = APIRouter()


@router.get("/health", dependencies=[Depends(verify_token)])
async def health_check():
    return {"status": "healthy"}
