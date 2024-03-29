from typing import (
    Any,
    Dict,
    Iterator,
    Sequence,
    Union,
    Optional,
    cast
    )
from typing_extensions import Self
from pydantic import(
    BaseModel,
    AnyHttpUrl,
    Field,
    root_validator,
    validator
    )
from datetime import datetime, timedelta, timezone
from .enumerators import CardType, CashbackType, CurrencyCode, enum_encoders
from ..abstract.caller_elements import BadRequest, RequestObjectABC, MonoCallerABC
from .utility import (
    align_datetime,
    default_timeframe,
    construct_bucket_list,
    TIMEBLOCK
    )


class HeadersPrivate(BaseModel):
    class Config:
        json_encoders=enum_encoders
        allow_population_by_field_name=True

    x_token: str = Field(alias="X-Token", title="X-Token")


class StatementReq(BaseModel, RequestObjectABC):
    class Config:
        json_encoders=enum_encoders

    account: str
    from_: Union[datetime, None] = None
    to_: Union[datetime, None] = None

    @root_validator
    def check_timeframe(cls, values):
        """Fixes the timeframe if wrong."""

        if values.get('to_') is None:
            tfr = default_timeframe()
            values['from_'] = tfr[0]
            values['to_'] = tfr[1]
        else:
            if values.get('from_') is None:
                tfr = default_timeframe(end_date=values['to_'])
                values['from_'] = tfr[0]
                values['to_'] = tfr[1]
            else:
                delta = values['to_'] - values['from_']
                valid_timeframe = int(delta.total_seconds()) > 0 and not int(delta.total_seconds()) > TIMEBLOCK.total_seconds()
                if not valid_timeframe:
                    values['from_'] = values['to_'] - TIMEBLOCK

        return values
    
    def get_path_tail(self):
        fr = str(int(self.from_.timestamp())) # type: ignore (set in validation)
        to = str(int(self.to_.timestamp())) # type: ignore (set in validation)
        ac = self.account
        return f'/personal/statement/{ac}/{fr}/{to}'


class UserInfoReq(RequestObjectABC):

    def get_path_tail(self):
        return '/personal/client-info'


class CurrRateReq(RequestObjectABC):

    def get_path_tail(self):
        return '/bank/currency'
    

class Transaction(BaseModel):
    class Config:
        json_encoders=enum_encoders

    id: str
    time: datetime
    description: str
    mcc: int
    hold: bool
    amount: int
    operationAmount: int
    currencyCode: CurrencyCode
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

    def __add__(self, other: Union[Self, 'Statement']) -> 'Statement':
        if isinstance(other, type(self)):
            both = [self, other]
            both.sort(key=lambda x: x.time)
            return Statement(transactions=both)
        else:
            try:
                # In case adding a Statement
                return other + self
            except TypeError:
                raise TypeError("Can only add Transaction or Statement to Transaction")

    def __hash__(self):
        return hash(self.id)


class TransactionArray(BaseModel):

    class Config:
        json_encoders=enum_encoders

    transactions: Sequence[Transaction]

    def __len__(self):
        return len(self.transactions)
    
    def __iter__(self) -> Iterator[Transaction]:
        """Returns an iterator over the transactions."""

        return iter(self.transactions)

    def __getitem__(self, index: int) -> Transaction:
        """Returns a transaction by index."""

        return self.transactions[index]

    def __hash__(self):
        return hash(tuple(self.transactions))


class Statement(TransactionArray):
    """:timeframe: represents the REAL range of dates in the statement,
    not necessarily the range of dates in the request.
    """

    class Config:
        json_encoders=enum_encoders


    timeframe: Sequence[datetime] = Field(default_factory=list)

    @root_validator
    def set_timeframe(cls, values: dict) -> dict:
        """Deduce the timeframe from the transactions."""
        if values['transactions']:
            start = values['transactions'][0].time
            end = values['transactions'][-1].time
            values['timeframe'] = (start, end)
        return values
        
    def __add__(self, other: Union[Self, 'Transaction']) -> Self:
        """Add two statements."""
        if isinstance(other, type(self)):
            tx = list(self.transactions) + list(other.transactions)
        elif isinstance(other, Transaction):
            tx = list(self.transactions) + [other,]
        else:
            raise TypeError("Can only add Transaction or Statement to Statement")
        tx.sort(key=lambda x: x.time)
        return Statement(transactions=tx)

    def to_dict(self) -> dict:
        """Returns a dictionary with Transaction ids as keys and Transaction objects as values."""

        return {item.id: item for item in self.transactions}
    
class TxBucket(TransactionArray):
    """Statements with defined timeframe length for caching purposes."""
    class Config:
        json_encoders=enum_encoders


    date: datetime

    
    @validator("date")
    def align_datetime(cls, v) -> datetime:
        """Aligns the date property to the nearest timeblock."""

        return align_datetime(v, TIMEBLOCK)
    
    @property
    def next(self) -> datetime:
        """Returns the name of the next bucket."""

        return self.date + TIMEBLOCK


class CacheableTransactionProvider(BaseModel):
    class Config:
        json_encoders=enum_encoders
    
    id: str
    balance: int
    currencyCode: CurrencyCode
    cached_statement: Dict[str, TxBucket] = dict()

    def getStatement(
        self,
        engine_instance: MonoCallerABC,
        fr: datetime,
        to: datetime,
        ) -> Statement:
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
                    statement = cast(Statement, engine_instance.make_request(req))
                    bucket = TxBucket(date=date, transactions=statement.transactions)
                    self.cached_statement[date.isoformat()] = bucket
                    relevant_buckets.insert(0, bucket)
                # BadRequest is returned by the API when requesting a timeframe that is too old.
                except BadRequest: # pragma: no cover
                    break # pragma: no cover

        whole_statement = list()
        for bucket in relevant_buckets:
            whole_statement.extend(bucket.transactions)
        whole_statement = [tx for tx in whole_statement if tx.time >= fr and tx.time <= to]
        whole_statement.sort(key=lambda x: x.time)

        return Statement(transactions=whole_statement, timeframe=(fr, to))


class Jar(CacheableTransactionProvider):
    class Config:
        json_encoders=enum_encoders

    sendId: str
    title: str
    description: Optional[str] = None
    goal: Optional[int] = None


class Account(CacheableTransactionProvider):
    class Config:
        json_encoders=enum_encoders

    creditLimit: int
    type: CardType
    cashbackType: CashbackType

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
    

class User(BaseModel):
    class Config:
        extra='ignore'
        json_encoders=enum_encoders
    
    clientId: str
    name: str
    accounts: Sequence[Account]
    jars: Sequence[Jar] 
    webHookURL: Optional[AnyHttpUrl] = None
    permissions: Optional[str] = None


class CurrencyExchange(BaseModel):
    class Config:
        json_encoders=enum_encoders

    currencyCodeA: int
    currencyCodeB: int
    date: datetime
    rateSell: Optional[float] = None
    rateBuy: Optional[float] = None
    rateCross: Optional[float] = None


class Currencies(BaseModel):
    class Config:
        json_encoders=enum_encoders

    rates: Sequence[CurrencyExchange]
