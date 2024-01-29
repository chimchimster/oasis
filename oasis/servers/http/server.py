import logging
import socket
import threading
import select

from oasis.exceptions.exc import InvalidHttpMethod
from oasis.http.request import RequestParser
from oasis.http.request.request_obj import Request
from oasis.route.register import REGISTERED_ROUTES, register_all

logger = logging.getLogger('Oasis Server')

register_all()


class SimpleHttpServer:

    allowed_methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}

    def __init__(self, addr: str, port: int):
        self.__addr = (addr, port)
        self.__server_socket = self.__create_socket()
        self.__shutdown_event = threading.Event()

    def __create_socket(self):
        server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.bind(self.__addr)
        server_socket.listen()
        return server_socket

    def start_serving(self):
        logger.info('Server started on http://%s:%s' % self.__addr)
        with self.__server_socket as soc:
            while not self.__shutdown_event.is_set():
                self.__accept_connection(soc)

    def __accept_connection(self, soc: socket.socket):

        rd, wr, er = select.select([soc], [], [], 1.0)
        for sk_rd in rd:
            if sk_rd is soc:
                try:
                    con, addr = sk_rd.accept()
                    addr: tuple
                    if con is not None:
                        logger.info('Received connection from %s:%s address.' % addr)
                        prc_con = threading.Thread(
                            target=self.__handle_client,
                            args=(con,),
                        )
                        prc_con.start()

                except OSError:
                    return

    def __handle_client(self, connection):

        while True:
            data = connection.recv(1024)
            if not data:
                connection.close()
                break
            else:
                decoded_data = data.decode('utf-8')
                pars = RequestParser(decoded_data)
                request_obj = pars.parse_http_request()
                return self.__handle_request(request_obj, connection)

    @classmethod
    def __handle_request(cls, request: Request, con):

        if request.method_name not in cls.allowed_methods:
            raise InvalidHttpMethod('Method %s is not allowed.' % request.method_name)

        handler = REGISTERED_ROUTES.get(request.route)
        print(handler)
        if handler is not None:
            data = handler()
            con.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + data)

        return

    def shutdown(self):

        self.__shutdown_event.set()

        logger.info('Server has been shut down.')

