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
