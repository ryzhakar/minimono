from datetime import datetime, timedelta
from time import sleep
import requests
from pydantic import BaseModel
from random import uniform as random_uniform
from .models import HeadersPrivate, CurrInfoResp, Transaction, UserInfoResp, StatementResp, CurrencyInfo
from .exceptions import ERRORS


class MonoCaller:

    base_url = 'https://api.monobank.ua'
    corresponding_methods = {
        "CurrRateReq": lambda x: CurrInfoResp(rates=[CurrencyInfo.parse_obj(n) for  n in x]),
        "UserInfoReq": lambda x: UserInfoResp.parse_obj(x),
        "StatementReq": lambda x: StatementResp(
            transactions=[Transaction.parse_obj(n) for n in x],
            ),
    }

    def __init__(self, token: str):
        self.headers = HeadersPrivate.parse_obj({"X-Token": token})
        self.last_request = datetime(1970, 1, 1)

    def ratecheck(self, last_request: datetime) -> None:
        """Checks if the rate limit is exceeded.
        If it is, sleeps for a random amount of time.
        """


        # Using a random delay to avoid being rate limited
        about_minute = random_uniform(60, 65)
        seconds_since_last_request = (datetime.now() - last_request).total_seconds()
        request_is_too_early = seconds_since_last_request < about_minute
        if  request_is_too_early:
            seconds = about_minute - seconds_since_last_request
            message = f"Rate limit exceeded. Waiting for {seconds} seconds."
            print(message)
            sleep(seconds)

        self.last_request = datetime.now()
            
    def make_request(self, request_obj) -> BaseModel:
        """Performs a request, specified via :request_obj:.
        Returns a model-encapsulated response object.
        """

        url = self.__class__.base_url + request_obj.get_path_tail()
        request_obj_name = request_obj.__class__.__name__
        response_method = self.__class__.corresponding_methods[request_obj_name]

        headers = self.headers.dict(by_alias=True)

        
        self.ratecheck(self.last_request)
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise ERRORS[response.status_code](response.json())

        encapsulated = response_method(response.json())
        return encapsulated
