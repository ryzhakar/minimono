class Error(Exception):
    pass

class EmptyStatement(Error):
    pass

class WrongObject(Error):
    pass