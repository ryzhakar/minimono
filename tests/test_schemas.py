from hypothesis import given, strategies as st
from pydantic import BaseModel
from typing import cast
from minimono.API.models import (
    Account,
    Transaction,
    User,
    Statement,
    CurrencyExchange,
    HeadersPrivate,
    StatementReq,
    TxBucket
)
from .strategies import b_any_model

@given(
    b_any_model
)
def test_roundtrip(inst):
    instance: BaseModel = inst
    assert instance == instance.parse_raw(instance.json())

@given(st.builds(Transaction))
def test_transaction_reduce(tr):
    reduced = tr.getReduced()
    d = tr.dict()
    assert all(
        d[key] == reduced[key]
        for key in reduced
    )

@given(st.builds(Statement), st.builds(Statement))
def test_statements_methods(s1, s2):
    import itertools

    s1 = cast(Statement, s1)
    s2 = cast(Statement, s2)
    s = s1 + s2
    
    assert len(s) == len(s1) + len(s2)
    assert all(x in s.transactions for x in itertools.chain(s1, s2))
    assert all(y == s[x] for x, y in enumerate(s))
    assert all(y in s.transactions for x, y in s.to_dict().items())


    
    