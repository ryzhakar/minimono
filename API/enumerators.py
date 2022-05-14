from enum import Enum
from iso4217 import Currency

class CardType(str, Enum):
    black = "black"
    white = "white"
    platinum = "platinum"
    iron = "iron"
    fop = "fop"
    yellow = "yellow"

class CashbackType(str, Enum):
    none = "None"
    uah = "UAH"
    miles = "Miles"
