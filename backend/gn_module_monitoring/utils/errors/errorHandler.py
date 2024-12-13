from geonature.utils.errors import GeonatureApiError


class InvalidUsage(GeonatureApiError):
    def __init__(self, message, status_code=400, payload=None):
        GeonatureApiError.__init__(self, message, status_code)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = {}
        rv["payload"] = self.payload
        rv["message"] = self.message
        rv["status_code"] = self.status_code
        return (rv, self.status_code)
