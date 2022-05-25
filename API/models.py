from typing import Any, Sequence
from datetime import datetime, timedelta
from pydantic import BaseModel, AnyHttpUrl, Field, root_validator
from .enumerators import CardType, CashbackType
from typing import Optional

def month_ago():
    return datetime.now() - timedelta(seconds=2682000.0)

class Account(BaseModel):
    id: str
    balance: int
    creditLimit: int
    type: CardType
    currencyCode: int
    cashbackType: CashbackType

class Jar(BaseModel):
    id: str
    sendId: str
    title: str
    currencyCode: int
    balance: int
    description: Optional[str] = None
    goal: Optional[int] = None

class Transaction(BaseModel):
    id: str
    time: datetime
    description: str
    mcc: int
    hold: bool
    amount: int
    operationAmount: int
    currencyCode: int
    commissionRate: int
    cashbackAmount: int
    balance: int
    receiptId: Optional[str] = None
    comment: Optional[int] = None
    counterEdrpou: Optional[str] = None
    counterIban: Optional[str] = None

class UserInfoResp(BaseModel):
    class Config:
        extra='ignore'
    
    clientId: str
    name: str
    accounts: Sequence[Account]
    jars: Sequence[Jar]
    webHookURL: Optional[AnyHttpUrl] = None
    permissions: Optional[str] = None


class StatementResp(BaseModel):
    statement_items: Sequence[Transaction]

class CurrencyInfo(BaseModel):
    currencyCodeA: int
    currencyCodeB: int
    date: datetime
    rateSell: Optional[float] = None
    rateBuy: Optional[float] = None
    rateCross: Optional[float] = None

class CurrInfoResp(BaseModel):
    rates: Sequence[CurrencyInfo]

class HeadersPrivate(BaseModel):
    x_token: str = Field(alias="X-Token", title="X-Token")

class StatementReq(BaseModel):
    account: str
    from_: datetime = Field(default_factory=month_ago)
    to_: datetime = Field(default_factory=datetime.now)

    @root_validator
    def check_timedelta(cls, values):
        fr = values['from_']
        to = values['to_']
        delta = to - fr
        if int(delta.total_seconds()) > 2682000:
            values['from_'] = to - timedelta(seconds=2682000)

        return values
    
    def get_path_tail(self):
        fr = str(int(self.from_.timestamp()))
        to = str(int(self.to_.timestamp()))
        ac = self.account
        return f'/personal/statement/{ac}/{fr}/{to}'

class UserInfoReq:

    @staticmethod
    def get_path_tail():
        return '/personal/client-info'

class CurrRateReq:

    @staticmethod
    def get_path_tail():
        return '/bank/currency'