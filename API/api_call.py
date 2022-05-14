import requests
from pydantic import BaseModel
from .models import HeadersPrivate, CurrInfoResp, UserInfoResp, StatementResp
from .exceptions import ERRORS


class MonoCaller:
    base_url = f'https://api.monobank.ua'
    request_response = {
        "CurrRatePath": CurrInfoResp,
        "UserInfoPath": UserInfoResp,
        "StatementPath": StatementResp
    }

    def __init__(self, token: str):
        self.headers = HeadersPrivate(x_token=token)

    def get_request(self, path_obj=None) -> BaseModel:
        url = self.__class__.base_url
        path_name = path_obj.__class__.__name__
        response_model = self.__class__.request_response['path_name']

        if path_obj:
            url += path_obj.get_path_tail()
        headers = self.headers.__dict__
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise ERRORS[response.status_code]

        modeled = response_model.parse_raw(response.json())
        return modeled
