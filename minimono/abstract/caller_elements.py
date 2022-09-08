from abc import ABC, abstractclassmethod
from pydantic import BaseModel

class RateLimited(Exception):
    pass

class NotFound(Exception):
    pass

class BadRequest(Exception):
    pass

class TimeConstraintError(Exception):
    pass

ERRORS = {
    404: NotFound,
    429: RateLimited,
    400: BadRequest
}


class RequestObjectABC(ABC): #pragma: no cover
    
    @abstractclassmethod
    def get_path_tail(self) -> str: #type: ignore
        pass

class MonoCallerABC(ABC): #pragma: no cover

    @abstractclassmethod
    def make_request(self, request_obj: RequestObjectABC) -> BaseModel: #type: ignore
        pass