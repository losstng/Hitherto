"""Basic API and system schemas for Hitherto."""

from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict
from datetime import datetime


class ApiResponse(BaseModel):
    """Standard API response structure."""
    success: bool = Field(..., description="Indicates if the API call was successful")
    data: Optional[Any] = Field(None, description="Payload returned if successful")
    error: Optional[str] = Field(None, description="Error message if success is False")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of response generation")


class TokenPayload(BaseModel):
    """OAuth token payload structure."""
    access_token: str
    refresh_token: Optional[str] = None  # may be absent if using implicit flow
    expires_at: datetime  # UNIX timestamp or ISO datetime
    scope: List[str]
    token_type: str


class HealthCheckResponse(BaseModel):
    """Health check response for modules and services."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    uptime_seconds: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    version: Optional[str] = None


class ModuleStatusResponse(BaseModel):
    """Module status response."""
    name: str
    status: str
    version: str
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    success_rate: Optional[float] = None
    error_message: Optional[str] = None
