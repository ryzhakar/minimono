class RateLimited(Exception):
    pass

class NotFound(Exception):
    pass

ERRORS = {
    404: NotFound,
    429: RateLimited,
}