"""Tests des schémas de l'API métier (validation)."""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "payment-si" / "api"))

from app.schemas import TransactionCreate  # noqa: E402


def test_valid_transaction():
    tx = TransactionCreate(source="a", destination="b", amount=Decimal("10.00"))
    assert tx.amount == Decimal("10.00")


def test_negative_amount_rejected():
    with pytest.raises(Exception):
        TransactionCreate(source="a", destination="b", amount=Decimal("-1"))


def test_zero_amount_rejected():
    with pytest.raises(Exception):
        TransactionCreate(source="a", destination="b", amount=Decimal("0"))
