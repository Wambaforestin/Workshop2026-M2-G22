"""Schémas Pydantic de l'API métier."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, condecimal


class AccountCreate(BaseModel):
    owner: str = Field(..., min_length=1, max_length=120)
    balance: condecimal(ge=0, max_digits=14, decimal_places=2) = Decimal("0")


class Account(BaseModel):
    id: str
    owner: str
    balance: Decimal


class TransactionCreate(BaseModel):
    source: str
    destination: str
    amount: condecimal(gt=0, max_digits=14, decimal_places=2)


class Transaction(BaseModel):
    id: str
    source: str
    destination: str
    amount: Decimal
    status: str
