from datetime import datetime, timedelta
from typing import Any
from .models import ActionableAccount, CurrInfoResp, StatementReq, UserInfoResp, StatementResp, UserInfoReq, CurrRateReq, default_timeframe
from .api_call import MonoCaller


class Client:

    def __init__(self, token, caller_class: Any = MonoCaller) -> None:
        """Initialize clients request engine."""

        self.engine = caller_class(token)
        self.user = self.engine.make_request(UserInfoReq())
        self.accounts = self.user.accounts

    def refreshUser(self):
        """Refresh user info."""

        self.user = self.engine.make_request(UserInfoReq())

    def getRates(self) -> CurrInfoResp:
        """Get currency rates."""

        return self.engine.make_request(CurrRateReq())

    def availableAccounts(self) -> list[ActionableAccount]:
        """Get available accounts."""

        return [self.accounts.__getattribute__(x[0]) for x in list(self.user.accounts.dict().items()) if x[1] is not None]

    def getStatement(
        self,
        account: ActionableAccount,
        from_time=(datetime.now() - timedelta(days=7)),
        to_time=datetime.now()
        ) -> StatementResp:
        return account.getStatement(self.engine, fr=from_time, to=to_time)