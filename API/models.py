from typing import Any, Iterator, Sequence, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, AnyHttpUrl, Field, root_validator, validator
from .enumerators import CardType, CashbackType
from .exceptions import BadRequest, TimeConstraintError, RateLimited
from typing import Optional


TIMEBLOCK = timedelta(days=31)

def align_datetime(date: datetime, align: timedelta) -> datetime:
    """Aligns a datetime to a certain timedelta."""

    aligned_timestamp = date.timestamp() // TIMEBLOCK.total_seconds() * TIMEBLOCK.total_seconds()
    return datetime.fromtimestamp(aligned_timestamp)


def default_timeframe(end_date: Optional[datetime]=None):
    if end_date is None:
        end_date =  datetime.now()
    to = end_date
    fr = datetime.now() - timedelta(seconds=2682000.0)

    if datetime(2017, 10, 1) > fr:
        raise TimeConstraintError('The oldest data API can provide is from 2017-10-01')
    
    return fr, to

def generate_timeframe_list(fr: datetime = datetime(2017, 10, 1), to: datetime = datetime.now()) -> Sequence[Sequence[datetime]]:
    """Returns a list of datetime pairs for timeframes."""

    timeframe_list = list()
    temp = to - timedelta(days=31)
    while temp > fr:
            timeframe_list.append((temp, to))
            to = temp
            temp -= timedelta(days=31)

    timeframe_list.append((fr, to))
    return timeframe_list
    

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
    comment: Optional[str] = None
    counterEdrpou: Optional[str] = None
    counterIban: Optional[str] = None

    def getReduced(self) -> dict:
        """Get a reduced transaction."""

        return {
            "id": self.id,
            "time": self.time,
            "description": self.description,
            "mcc": self.mcc,
            "amount": self.amount,
        }

class StatementResp(BaseModel):
    statement_items: Sequence[Transaction] = Field(default_factory=list)
    timeframe: Sequence[datetime] = Field(default_factory=tuple)

    @root_validator(pre=True)
    def set_timeframe(cls, values: dict) -> dict:
        """Deduce the timeframe from the transactions."""

        values['timeframe'] = (values['statement_items'][0].time, values['statement_items'][-1].time)
        return values

    def __add__(self, other: Any) -> 'StatementResp':
        """Add two statements."""

        return StatementResp(statement_items=self.statement_items + other.statement_items)

    def __iter__(self) -> Iterator[Transaction]:
        """Returns an iterator over the transactions."""

        return iter(self.statement_items)

    def __getitem__(self, index: int) -> Transaction:
        """Returns a transaction by index."""

        return self.statement_items[index]

    def to_dict(self) -> dict:
        """Returns a dictionary with Transaction ids as keys and Transaction objects as values."""

        return {item.id: item for item in self.statement_items}
    
class Jar(BaseModel):
    id: str
    sendId: str
    title: str
    currencyCode: int
    balance: int
    description: Optional[str] = None
    goal: Optional[int] = None


class StatementBucket(BaseModel):
    """Statements with defined timeframe length for caching purposes."""

    full: bool = False
    timeframe: Sequence[datetime]
    transactions: Sequence[Transaction] = Field(default_factory=list)

    @validator("timeframe")
    def align_timeframe(cls, v) -> Sequence[datetime]:
        """Aligns the timeframe to the nearest timeblock."""

        fr, to = v[0], v[1]
        fr = align_datetime(fr, TIMEBLOCK)
        to = (fr + TIMEBLOCK)
        v = (fr, to)
        return v

    @property
    def name(self) -> str:
        """Returns the name of the bucket."""

        return self.timeframe[0].isoformat()

    def __iter__(self) -> Iterator[Transaction]:
        """Returns an iterator over the transactions."""

        return iter(self.transactions)

    def __getitem__(self, index: int) -> Transaction:
        """Returns a transaction by index."""

        return self.transactions[index]


class Account(BaseModel):
    id: str
    balance: int
    creditLimit: int
    type: CardType
    currencyCode: int
    cashbackType: CashbackType
    _cached_Statement: dict = Field(default_factory=dict)
    
    def getStatement(
        self,
        engine_instance,
        fr: datetime = datetime(2017, 10, 1),
        to: datetime = datetime.now()
        ) -> StatementResp:
        """Get the statement between dates."""

        reqs = [
            StatementReq(account=self.id, from_=x[0], to_=x[1])
            for x in generate_timeframe_list(fr=fr, to=to)
            ]

        whole_statement = StatementResp()
        for req in reqs:
            try:
                consequent_month = engine_instance.make_request(req)
                print('-', sep='', end='')
                whole_statement = consequent_month + whole_statement

            # BadRequest is returned by the API when requesting a timeframe that is too old.
            except BadRequest:
                break

        self.statement = whole_statement
        return whole_statement


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
        mapping = {setters[x['type']](x): Account.parse_obj(x) for x in sequence_of_accounts}
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
        """Fixes the timeframe if wrong."""

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