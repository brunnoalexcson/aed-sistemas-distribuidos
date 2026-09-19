"""Modelos de dados do sistema de biblioteca."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str
    available: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "available": self.available,
        }


@dataclass
class User:
    id: int
    name: str
    email: str
    active: bool = True
    pending_fine: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "active": self.active,
            "pending_fine": round(self.pending_fine, 2),
        }


@dataclass
class Loan:
    id: int
    book_id: int
    user_id: int
    loan_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    status: str = "open"  # "open" ou "returned"
    fine_amount: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "user_id": self.user_id,
            "loan_date": self.loan_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "status": self.status,
            "fine_amount": round(self.fine_amount, 2),
        }
