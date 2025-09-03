from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Record  # noqa: F401 ensure model is imported so table is created
from .schemas import RecordCreate, RecordOut, RecordUpdate
from . import services

# Initialize DB (create tables)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Record Management API",
    description=(
        "RESTful CRUD API for managing records. "
        "Includes simple business rules and uses SQLite for persistence."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "Health", "description": "Service health and diagnostics."},
        {"name": "Records", "description": "CRUD operations for records."},
    ],
)

# CORS - allow all for development; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, configure specific origins via env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """
    Health check endpoint to confirm the service is running.
    Returns a simple JSON payload.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/records",
    response_model=List[RecordOut],
    tags=["Records"],
    summary="List records",
    description="Returns a list of records. Optionally filter by status.",
)
def list_records(
    status: Optional[str] = Query(
        default=None,
        description="Optional status filter (e.g., 'active', 'archived').",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns all records ordered by created_at descending.
    """
    return services.list_records(db=db, status=status)


# PUBLIC_INTERFACE
@app.post(
    "/records",
    response_model=RecordOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Records"],
    summary="Create a record",
    description="Creates a new record after validating business rules.",
    responses={
        400: {"description": "Validation or business rule violation."},
        409: {"description": "Conflict due to business rules (e.g., duplicate active title)."},
    },
)
def create_record(payload: RecordCreate, db: Session = Depends(get_db)):
    """
    Create a new record. Title among active records must be unique.
    """
    try:
        rec = services.create_record(db=db, payload=payload)
        return rec
    except ValueError as e:
        # Business rule violation
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# PUBLIC_INTERFACE
@app.get(
    "/records/{record_id}",
    response_model=RecordOut,
    tags=["Records"],
    summary="Get a single record",
    description="Retrieves a record by its ID.",
    responses={404: {"description": "Record not found."}},
)
def get_record(
    record_id: int = Path(..., description="The ID of the record."),
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific record by ID.
    """
    rec = services.get_record(db=db, record_id=record_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return rec


# PUBLIC_INTERFACE
@app.put(
    "/records/{record_id}",
    response_model=RecordOut,
    tags=["Records"],
    summary="Update a record",
    description="Updates an existing record. Partial fields supported.",
    responses={
        404: {"description": "Record not found."},
        409: {"description": "Conflict due to business rules (e.g., duplicate active title)."},
    },
)
def update_record(
    record_id: int = Path(..., description="The ID of the record to update."),
    changes: RecordUpdate = ...,
    db: Session = Depends(get_db),
):
    """
    Update a record by applying provided changes.
    """
    try:
        rec = services.update_record(db=db, record_id=record_id, changes=changes)
        return rec
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# PUBLIC_INTERFACE
@app.delete(
    "/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Records"],
    summary="Delete a record",
    description="Deletes a record by ID.",
    responses={
        204: {"description": "Record deleted."},
        404: {"description": "Record not found."},
    },
)
def delete_record(
    record_id: int = Path(..., description="The ID of the record to delete."),
    db: Session = Depends(get_db),
):
    """
    Delete a record by ID.
    """
    deleted, _ = services.delete_record(db=db, record_id=record_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return None
