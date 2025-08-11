"""Pydantic models for request and response bodies.

These dataclasses define the shapes of the JSON objects accepted and returned
by the API endpoints.  They enforce type checking and validation at runtime.
"""

from datetime import datetime, date, time
from typing import Optional, Literal

from pydantic import BaseModel, Field, validator


class SignUpRequest(BaseModel):
    """Request body for user registration."""

    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="Plain-text password (development only)")

    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Basic email validation to avoid dependency on `email_validator`.

        This check is intentionally simple and only ensures that the string
        contains an `@` and a dot after the `@`.  Production code should
        perform more robust validation or use a dedicated library.
        """
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


class UserResponse(BaseModel):
    """Response returned after user registration or login."""

    id: str
    email: str
    points: int


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: str
    password: str

    @validator("email")
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


class InquiryRequest(BaseModel):
    """Request body for the universal inquiry endpoint."""

    question: str = Field(..., description="A natural-language question posed by the user")


class InquiryResponse(BaseModel):
    """Response from the universal inquiry endpoint."""

    answer: str
    points_remaining: int


class QuantificationRequest(BaseModel):
    """Request for the Qimen Quantification analysis."""

    crypto: Literal['btc', 'eth'] = Field(..., description="Cryptocurrency symbol (btc or eth)")


class FinanceRequest(BaseModel):
    """Request for the Qimen Finance analysis."""

    # Currently no fields are required; the analysis is based on current time.
    pass


class DestinyRequest(BaseModel):
    """Request for the Qimen Destiny analysis."""

    birth_date: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    birth_time: time = Field(..., description="Time of birth (HH:MM)")


class AnalysisResponse(BaseModel):
    """Generic response for analysis endpoints."""

    result: str
    points_remaining: int


class PointsResponse(BaseModel):
    """Response containing the user's current point balance."""

    user_id: str
    points: int


class PointsSpendRequest(BaseModel):
    """Request to deduct points from a user's balance."""

    amount: int = Field(..., gt=0, description="Number of points to deduct")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str