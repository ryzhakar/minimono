from enum import Enum

class CardType(str, Enum):
    black = "black"
    white = "white"
    platinum = "platinum"
    iron = "iron"
    fop = "fop"
    yellow = "yellow"
    eAid = "eAid"
    eur = "eur"
    usd = "usd"

class CashbackType(str, Enum):
    none = "None"
    uah = "UAH"
    miles = "Miles"

class CurrencyCode(int, Enum):
    black = 980
    eur = 978
    usd = 840

enum_encoders = {
    CardType: lambda x: x.value,
    CashbackType: lambda x: x.value,
    CurrencyCode: lambda x: x.value,
}