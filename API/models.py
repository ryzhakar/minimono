from typing import Any, Sequence, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, AnyHttpUrl, Field, root_validator, validator
from .enumerators import CardType, CashbackType
from typing import Optional

def default_timeframe(end_date: Optional[datetime]=None):
    if end_date is None:
        end_date =  datetime.now()
    to = end_date
    fr = datetime.now() - timedelta(seconds=2682000.0)
    
    return fr, to

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

class StatementResp(BaseModel):
    statement_items: Sequence[Transaction]

class Account(BaseModel):
    id: str
    balance: int
    creditLimit: int
    type: CardType
    currencyCode: int
    cashbackType: CashbackType

class ActionableAccount(Account):
    def getStatement(self, engine_instance, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> StatementResp:        
        return engine_instance.make_request(StatementReq(account=self.id, from_=start_date, to_=end_date))

class MultipleAccounts(BaseModel):
    black: Union[Account, None] = None
    usd: Union[Account, None] = None
    eur: Union[Account, None] = None
    white: Union[Account, None] = None
    platinum: Union[Account, None] = None
    iron: Union[Account, None] = None
    fop: Union[Account, None] = None
    yellow: Union[Account, None] = None
    eAid: Union[Account, None] = None

    @classmethod
    def map_from_sequence(cls, sequence_of_accounts: Sequence[dict]):
        curr = {
            980: 'black',
            978: 'eur',
            840: 'usd',
        }
        setters = {
            CardType.black: lambda x: curr[x['currencyCode']],
            CardType.white: lambda x: "white",
            CardType.platinum: lambda x: "platinum",
            CardType.iron: lambda x: "iron",
            CardType.fop: lambda x: "fop",
            CardType.yellow: lambda x: "yellow",
            CardType.eAid: lambda x: "eAid",
        }
        mapping = {setters[x['type']](x): ActionableAccount.parse_obj(x) for x in sequence_of_accounts}
        return cls.parse_obj(mapping)

class UserInfoResp(BaseModel):
    class Config:
        extra='ignore'
    
    clientId: str
    name: str
    accounts: MultipleAccounts
    jars: Sequence[Jar]
    webHookURL: Optional[AnyHttpUrl] = None
    permissions: Optional[str] = None

    @validator('accounts', pre=True)
    def map_accounts(cls, v):
        return MultipleAccounts.map_from_sequence(v)

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
    from_: Union[datetime, None] = None
    to_: Union[datetime, None] = None

    @root_validator
    def check_timeframe(cls, values): 
        if values['to_'] is None:
            tfr = default_timeframe()
            values['from_'] = tfr[0]
            values['to_'] = tfr[1]
        else:
            if values['from_'] is None:
                tfr = default_timeframe(end_date=values['to_'])
                values['from_'] = tfr[0]
                values['to_'] = tfr[1]
            else:
                delta = values['to_'] - values['from_']
                valid_timeframe = int(delta.total_seconds()) > 0 and not int(delta.total_seconds()) > 2682000
                if not valid_timeframe:
                    values['from_'] = values['to_'] - timedelta(seconds=2682000)

        return values
    
    def get_path_tail(self):
        fr = str(int(self.from_.timestamp())) # type: ignore
        to = str(int(self.to_.timestamp())) # type: ignore
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