from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json, os
from models import TokenPayload
from database import get_db

router = APIRouter()

TOKEN_FILE = "token.json"

@router.post("/auth/token")
def receive_token(payload: TokenPayload, db: Session = Depends(get_db)):
    """
    Called by frontend after OAuth. Saves the token payload to disk.
    """
    try:
        # Convert Pydantic model to plain dict, then JSON-dump
        token_data = payload.dict()
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save token: {e}")