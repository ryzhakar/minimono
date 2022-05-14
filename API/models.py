from typing import Any, Sequence
from datetime import datetime, timedelta
from pydantic import BaseModel, AnyHttpUrl, Field, root_validator
from .enumerators import CardType, CashbackType, Currency
from typing import Optional

def month_ago():
    dt = datetime.now()
    dt = int(dt.timestamp())
    return dt - 2682000

class Account(BaseModel):
    id: str
    balance: int
    creditLimit: int
    type: CardType
    currencyCode: Currency
    cashbackType: CashbackType

class Transaction(BaseModel):
    id: str
    time: datetime
    description: str
    mcc: int
    hold: bool
    amount: int
    operationAmount: int
    currencyCode: Currency
    commissionRate: int
    cashbackAmount: int
    balance: int
    receiptId: str
    comment: Optional[int]
    counterEdrpou: Optional[str] = None
    counterIban: Optional[str] = None

class UserInfoResp(BaseModel):
    id: str
    name: str
    webHookURL: AnyHttpUrl
    accounts: Sequence[Account]

class StatementResp(BaseModel):
    statement_items: Sequence[Transaction]

class CurrencyInfo(BaseModel):
    currencyCodeA: Currency
    currencyCodeB: Currency
    date: datetime
    rateSell: float
    rateBuy: float
    rateCross: float

class CurrInfoResp(BaseModel):
    rates: Sequence[CurrencyInfo]

class HeadersPrivate(BaseModel):
    x_token: str

class StatementPath(BaseModel):
    account: str
    from_: datetime = Field(default_factory=month_ago)
    to_: datetime = Field(default_factory=datetime.now)

    @root_validator(always=True)
    def check_timedelta(cls, values):
        fr = values['from_']
        to = values['to_']
        delta = to - fr
        if not int(delta.total_seconds) <= 2682000:
            values['from_'] = to - timedelta(seconds=2682000)

        return values
    
    def get_path_tail(self):
        fr = str(int(self.from_.timestamp()))
        to = str(int(self.to_.timestamp()))
        ac = self.account
        return f'/personal/statement/{ac}/{fr}/{to}'

class UserInfoPath:
    path = '/personal/client-info'

    def get_path_tail(self):
        return self.__class__.path

class CurrRatePath:
    path = '/bank/currency'

    def get_path_tail(self):
        return self.__class__.path