from hypothesis import given, strategies as st
from pydantic import BaseModel
from minimono.API.models import (
    Account,
    Transaction,
    UserInfoResp,
    StatementResp,
    CurrencyInfo,
    HeadersPrivate,
    TxBucket
)
from .strategies import b_any_model

@given(
    b_any_model
)
def test_roundtrip(inst):
    instance: BaseModel = inst
    assert instance == instance.parse_raw(instance.json())
