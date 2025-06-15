from pydantic import BaseModel, Field
from typing import Optional, Union, Any
from datetime import datetime


class ApiResponse(BaseModel):
    success: bool = Field(..., description="Indicates if the API call was successful")
    data: Optional[Any] = Field(None, description="Payload returned if successful")
    error: Optional[str] = Field(None, description="Error message if success is False")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of response generation")