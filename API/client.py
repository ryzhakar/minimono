from datetime import datetime
from typing import Any, Optional
from .models import Account, CurrInfoResp, StatementReq, UserInfoResp, StatementResp, UserInfoReq, CurrRateReq, default_timeframe
from .api_call import MonoCaller


class Client:

    def __init__(self, token, caller_class: Any = MonoCaller) -> None:
        self.engine = caller_class(token)
        self.user = self.engine.make_request(UserInfoReq())

    def refreshUser(self):
        self.user = self.engine.make_request(UserInfoReq())

    def getRates(self) -> CurrInfoResp:
        return self.engine.make_request(CurrRateReq())
    
