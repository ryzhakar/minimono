import requests
from datetime import datetime
from time import sleep
from pydantic import BaseModel
from random import uniform as random_uniform
from .. import abstract, models


class MonoCaller(abstract.MonoCallerABC):

    base_url = 'https://api.monobank.ua'
    corresponding_methods = {
        "CurrRateReq": lambda x: models.Currencies(rates=[models.CurrencyExchange.parse_obj(n) for  n in x]),
        "UserInfoReq": lambda x: models.User.parse_obj(x),
        "StatementReq": lambda x: models.Statement(
            transactions=[models.Transaction.parse_obj(n) for n in x],
            ),
    }

    def __init__(self, token: str, self_ratelimit: bool = True):
        self.headers = models.HeadersPrivate.parse_obj({"X-Token": token})
        self.last_request = datetime(1970, 1, 1)
        self.self_ratelimit = self_ratelimit

    def _ratecheck(self) -> None:
        """Checks if the rate limit is exceeded.
        If it is, sleeps for a random amount of time.
        """

        last_request = self.last_request
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

        if self.self_ratelimit:
            self._ratecheck()
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200: # pragma: no cover
            raise abstract.ERRORS[response.status_code](response.json())

        encapsulated = response_method(response.json())
        return encapsulated
