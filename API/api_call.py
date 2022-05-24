import requests
from pydantic import BaseModel
from .models import HeadersPrivate, CurrInfoResp, UserInfoResp, StatementResp
from .exceptions import ERRORS


class MonoCaller:

    base_url = 'https://api.monobank.ua'
    request_response = {
        "CurrRatePath": CurrInfoResp,
        "UserInfoPath": UserInfoResp,
        "StatementPath": StatementResp,
    }

    def __init__(self, token: str):
        self.headers = HeadersPrivate.parse_obj({"X-Token": token})

    def get_request(self, path_obj) -> BaseModel:
        url = self.__class__.base_url + path_obj.get_path_tail()
        path_obj_name = path_obj.__class__.__name__
        response_model = self.__class__.request_response[path_obj_name]


        headers = self.headers.dict(by_alias=True)
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise ERRORS[response.status_code](response.json())

        modeled = response_model.parse_obj(response.json())
        return modeled
