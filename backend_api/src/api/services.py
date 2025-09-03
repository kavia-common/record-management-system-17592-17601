"""
Business logic layer for managing records.
Encapsulates rules and provides functions consumed by API routes.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Record
from .schemas import RecordCreate, RecordUpdate


# PUBLIC_INTERFACE
def list_records(db: Session, status: Optional[str] = None) -> List[Record]:
    """
    Returns a list of records, optionally filtered by status.
    Business rule: Results are ordered by created_at descending.
    """
    stmt = select(Record)
    if status:
        stmt = stmt.where(Record.status == status)
    stmt = stmt.order_by(Record.created_at.desc())
    return list(db.scalars(stmt).all())


# PUBLIC_INTERFACE
def create_record(db: Session, payload: RecordCreate) -> Record:
    """
    Creates a new record applying business rules:
    - Title must be unique among 'active' records.
    - Default status is 'active' if not provided.
    """
    # Enforce a simple uniqueness rule for active titles:
    if payload.status == "active":
        existing = db.scalar(
            select(Record).where(Record.title == payload.title, Record.status == "active")
        )
        if existing:
            raise ValueError("A record with this title already exists in active status.")

    rec = Record(
        title=payload.title,
        description=payload.description,
        status=payload.status or "active",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# PUBLIC_INTERFACE
def get_record(db: Session, record_id: int) -> Optional[Record]:
    """
    Fetches a single record by id.
    """
    return db.get(Record, record_id)


# PUBLIC_INTERFACE
def update_record(db: Session, record_id: int, changes: RecordUpdate) -> Record:
    """
    Updates a record by applying provided changes.
    Business rules:
    - If updating title to a value that exists in another active record, prevent duplicate among active.
    - Status transition allowed between any values; no special restriction here.
    """
    rec = db.get(Record, record_id)
    if not rec:
        raise LookupError("Record not found")

    new_title = changes.title if changes.title is not None else rec.title
    new_status = changes.status if changes.status is not None else rec.status

    if new_status == "active":
        conflict = db.scalar(
            select(Record).where(
                Record.title == new_title,
                Record.status == "active",
                Record.id != rec.id,
            )
        )
        if conflict:
            raise ValueError("Another active record with this title already exists.")

    if changes.title is not None:
        rec.title = changes.title
    if changes.description is not None:
        rec.description = changes.description
    if changes.status is not None:
        rec.status = changes.status

    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# PUBLIC_INTERFACE
def delete_record(db: Session, record_id: int) -> Tuple[bool, Optional[int]]:
    """
    Deletes a record by id. Returns a tuple (deleted, id).
    """
    rec = db.get(Record, record_id)
    if not rec:
        return False, None
    db.delete(rec)
    db.commit()
    return True, record_id
