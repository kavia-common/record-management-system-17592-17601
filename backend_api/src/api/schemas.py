"""
Pydantic schemas (DTOs) for request and response payloads.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr


class RecordBase(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(
        ..., description="The title of the record."
    )
    description: Optional[str] = Field(
        None, description="Optional detailed description for the record."
    )
    status: constr(strip_whitespace=True, min_length=1, max_length=50) = Field(
        "active", description="Status of the record. Example values: active, archived."
    )


class RecordCreate(RecordBase):
    """
    Payload for creating a record. All fields are validated by RecordBase.
    """
    pass


class RecordUpdate(BaseModel):
    """
    Partial update payload for a record.
    """
    title: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = Field(
        None, description="New title for the record."
    )
    description: Optional[str] = Field(
        None, description="New description for the record."
    )
    status: Optional[constr(strip_whitespace=True, min_length=1, max_length=50)] = Field(
        None, description="New status for the record."
    )


class RecordOut(BaseModel):
    id: int = Field(..., description="Unique ID of the record.")
    title: str = Field(..., description="The title of the record.")
    description: Optional[str] = Field(None, description="Record description.")
    status: str = Field(..., description="Current status of the record.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    class Config:
        from_attributes = True
