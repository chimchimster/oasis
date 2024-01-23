import re

from .exc import *


class RequestParser:
    def __init__(self, req_data: str):
        self.__req_data = [row.strip() for row in req_data.split('\n') if row.strip()]

    def parse_http_request(self) -> dict:

        try:
            return {
                'method': self.__parse_method(),
                'route': self.__parse_route(),
                'proto': self.__parse_proto(),
                **self.__parse_headers(),
            }
        except (InvalidRequest, InvalidHttpMethod, InvalidProtocol, InvalidRoute):
            return {
                'status_code': 400,
                'detail': 'Bad request.',
            }

    def __parse_method(self):
        if self.__req_data:
            if method := re.match(r'(GET|POST|PUT|DELETE)', self.__req_data[0]):
                return method.group()
            else:
                raise InvalidHttpMethod('HTTP method is invalid.')
        else:
            raise InvalidRequest('Invalid request.')

    def __parse_route(self):
        if self.__req_data:
            if route := re.search(r'\s(.*?)\s', self.__req_data[0]):
                return route.group().strip()
            else:
                raise InvalidRoute('Route is invalid.')
        else:
            raise InvalidRequest('Invalid request')

    def __parse_proto(self):
        if self.__req_data:
            if proto := re.search(r'HTTP.*', self.__req_data[0]):
                return proto.group().strip()
            else:
                raise InvalidProtocol('Protocol is invalid.')
        else:
            raise InvalidRequest('Invalid request.')

    def __parse_headers(self):

        headers = {}
        for row in [r for r in self.__req_data[1:] if r]:
            row = row.strip()
            key, value = re.split(':\s', row, maxsplit=1)
            headers[key] = value

        return headers


