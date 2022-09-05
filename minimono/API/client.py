from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from .models import (
    Account,
    CurrInfoResp,
    UserInfoResp,
    StatementResp,
    UserInfoReq,
    CurrRateReq,
)
from .api_call import MonoCaller


class Client:

    def saveFile(self):
        """Save user info (including cached accounts) to file."""

        jsonified = self.user.json(indent=2, ensure_ascii=False)
        with open(f"{self.user.clientId}.json", "w+") as f:
            f.write(jsonified)

    def loadFile(self, file_name: str):
        with open(file_name, "r") as f:
            self.user = UserInfoResp.parse_raw(f.read())

    def __init__(
        self,
        token: str,
        caller_class: Any = MonoCaller,
        load_file: Optional[str] = None
        ) -> None:
        """Initialize clients request engine."""

        self.engine = caller_class(token)
        if load_file is not None:
            self.loadFile(load_file)
        else:
            self.user = self.engine.make_request(UserInfoReq())
        
    def refreshUser(self):
        """Refresh user info from API. Loses cached accounts."""
        
        self.user = self.engine.make_request(UserInfoReq())

    def getRates(self) -> CurrInfoResp:
        """Get currency rates."""

        return self.engine.make_request(CurrRateReq())

    def getStatement(
        self,
        account: Account,
        from_time=(datetime.now(tz=timezone.utc) - timedelta(days=7)),
        to_time=datetime.now(tz=timezone.utc)
        ) -> StatementResp:
        return account.getStatement(self.engine, fr=from_time, to=to_time)

    @property
    def accounts(self) -> Dict[str, Account]:
        """Get accounts."""
        mapping = {
            x.type.name: x for x in self.user.accounts
        }

        return mapping

    def __getitem__(self, key: str) -> Account:
        """Get account by type."""
        acc = self.accounts.get(key)
        if acc is None:
            acc_str = ' ,'.join(list(self.accounts.keys()))
            message = f"Account {key} not found. Try one of these: {acc_str}"
            raise KeyError(message)
        return self.accounts[key]

    def __eq__(self, other: Any) -> bool:
        """Compare clients."""
        if not isinstance(other, Client):
            return False
        else:
            return self.user == other.user