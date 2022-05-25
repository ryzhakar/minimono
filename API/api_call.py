import requests
from pydantic import BaseModel
from .models import HeadersPrivate, CurrInfoResp, Transaction, UserInfoResp, StatementResp, CurrencyInfo
from .exceptions import ERRORS


class MonoCaller:

    base_url = 'https://api.monobank.ua'
    request_response = {
        "CurrRatePath": lambda x: CurrInfoResp(rates=[CurrencyInfo.parse_obj(n) for  n in x]),
        "UserInfoPath": lambda x: UserInfoResp.parse_obj(x),
        "StatementPath": lambda x: StatementResp(statement_items=[Transaction.parse_obj(n) for n in x]),
    }

    def __init__(self, token: str):
        self.headers = HeadersPrivate.parse_obj({"X-Token": token})

    def get_request(self, path_obj) -> BaseModel:
        """Performs a request, specified via :path_obj:.
        Returns a model-encapsulated response object.
        """

        url = self.__class__.base_url + path_obj.get_path_tail()
        path_obj_name = path_obj.__class__.__name__
        response_method = self.__class__.request_response[path_obj_name]

        headers = self.headers.dict(by_alias=True)
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise ERRORS[response.status_code](response.json())

        encapsulated = response_method(response.json())
        return encapsulated
