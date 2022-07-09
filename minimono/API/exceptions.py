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