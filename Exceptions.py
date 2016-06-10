

class Error(Exception):
    def __init__(self,msg):
        Exception.__init__(self,msg)

class InternalError(Error):
    def __init__(self,msg):
        Error.__init__(self,msg)

