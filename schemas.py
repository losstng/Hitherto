from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime

class ApiResponse(BaseModel):
    success: bool = Field(..., description="Indicates if the API call was successful")
    data: Optional[Any] = Field(None, description="Payload returned if successful")
    error: Optional[str] = Field(None, description="Error message if success is False")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of response generation")

class TokenPayload(BaseModel):
    access_token: str
    refresh_token: Optional[str]  # may be absent if using implicit flow
    expires_at: datetime          # UNIX timestamp or ISO datetime
    scope: List[str]
    token_type: str
