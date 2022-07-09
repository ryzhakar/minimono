from typing import (
    Any,
    Dict,
    Iterator,
    Sequence,
    Union,
    Optional
    )
from datetime import datetime, timedelta, timezone
from pydantic import(
    BaseModel,
    AnyHttpUrl,
    Field,
    root_validator,
    validator
    )
from .enumerators import CardType, CashbackType
from .exceptions import BadRequest
from .utility import (
    align_datetime,
    default_timeframe,
    construct_bucket_list,
    TIMEBLOCK
    )


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
    """:timeframe: represents the REAL range of dates in the statement,
    not necessarily the range of dates in the request.
    """

    transactions: Sequence[Transaction] = Field(default_factory=list)
    timeframe: Sequence[datetime] = Field(default_factory=tuple)

    @root_validator
    def set_timeframe(cls, values: dict) -> dict:
        """Deduce the timeframe from the transactions."""
        if values['transactions']:
            start = values['transactions'][0].time
            end = values['transactions'][-1].time
            values['timeframe'] = (start, end)
        return values

    def __add__(self, other: Any) -> 'StatementResp':
        """Add two statements."""

        tx = self.transactions + other.transactions
        tx.sort(key=lambda x: x.time)
        return StatementResp(transactions=tx)

    def __iter__(self) -> Iterator[Transaction]:
        """Returns an iterator over the transactions."""

        return iter(self.transactions)

    def __getitem__(self, index: int) -> Transaction:
        """Returns a transaction by index."""

        return self.transactions[index]

    def to_dict(self) -> dict:
        """Returns a dictionary with Transaction ids as keys and Transaction objects as values."""

        return {item.id: item for item in self.transactions}
    
class Jar(BaseModel):
    id: str
    sendId: str
    title: str
    currencyCode: int
    balance: int
    description: Optional[str] = None
    goal: Optional[int] = None


class TxBucket(BaseModel):
    """Statements with defined timeframe length for caching purposes."""

    date: datetime
    transactions: Sequence[Transaction] = Field(default_factory=list)
    
    @validator("date")
    def align_datetime(cls, v) -> datetime:
        """Aligns the date property to the nearest timeblock."""

        return align_datetime(v, TIMEBLOCK)
    
    @property
    def next(self) -> datetime:
        """Returns the name of the next bucket."""

        return self.date + TIMEBLOCK

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
    cached_statement: Dict[str, TxBucket] = dict()

    @root_validator(pre=True)
    def coerce_right_type(cls, keywords: Dict) -> Dict:
        curr = {
            980: CardType.black,
            978: CardType.eur,
            840: CardType.usd,
        }
        setters = {
            "black": lambda x: curr[x['currencyCode']],
            "white": lambda x: CardType.white,
            "platinum": lambda x: CardType.platinum,
            "iron": lambda x: CardType.iron,
            "fop": lambda x: CardType.fop,
            "yellow": lambda x: CardType.yellow,
            "eAid": lambda x: CardType.eAid,
            "eur": lambda x: CardType.eur,
            "usd": lambda x: CardType.usd,
        }
        curr_type = keywords['type']
        type_retriever = setters[curr_type]
        valid_type = type_retriever(keywords)
        keywords['type'] = valid_type
        return keywords
    
    def getStatement(
        self,
        engine_instance,
        fr: datetime,
        to: datetime,
        ) -> StatementResp:
        """Get the statement between dates using cached values where possible.
        Tz-info must be UTC.
        """

        wrong_timezone = to.tzinfo is not timezone.utc or fr.tzinfo is not timezone.utc
        if wrong_timezone:
            raise ValueError("Timezone must be UTC.")

        relevant_buckets = list()
        dates = construct_bucket_list(fr=fr, to=to)

        for date in dates:
            cached = date.isoformat() in self.cached_statement
            if cached:
                bucket = self.cached_statement[date.isoformat()]
                relevant_buckets.insert(0, bucket)
            else:
                end_date = date + TIMEBLOCK
                if to < end_date:
                    end_date = to

                try:
                    req = StatementReq(
                        account=self.id, from_=date, to_=date + TIMEBLOCK
                    )
                    statement = engine_instance.make_request(req)
                    bucket = TxBucket(date=date, transactions=statement.transactions)
                    self.cached_statement[date.isoformat()] = bucket
                    relevant_buckets.insert(0, bucket)
                # BadRequest is returned by the API when requesting a timeframe that is too old.
                except BadRequest:
                    pass

        whole_statement = list()
        for bucket in relevant_buckets:
            whole_statement.extend(bucket.transactions)
        whole_statement = [tx for tx in whole_statement if tx.time >= fr and tx.time <= to]
        whole_statement.sort(key=lambda x: x.time)

        return StatementResp(transactions=whole_statement, timeframe=(fr, to))

class UserInfoResp(BaseModel):
    class Config:
        extra='ignore'
    
    clientId: str
    name: str
    accounts: Sequence[Account]
    jars: Sequence[Jar] 
    webHookURL: Optional[AnyHttpUrl] = None
    permissions: Optional[str] = None


class CurrencyInfo(BaseModel):
    currencyCodeA: int
    currencyCodeB: int
    date: datetime
    rateSell: Optional[float] = None
    rateBuy: Optional[float] = None
    rateCross: Optional[float] = None


class CurrInfoResp(BaseModel):
    rates: Sequence[CurrencyInfo]
