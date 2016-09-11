import socket
import unittest


class CaesarCipherServerTests(unittest.TestCase):
    _host = '127.0.0.1'
    _server_port = 55555
    _sock = None

    def setUp(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def tearDown(self):
        self._sock.close()

    def test_able_to_connect_to_server(self):
        try:
            self._sock.connect((self._host, self._server_port))
        except Exception as e:
            self.fail('Unable to connect to server on port ' +
                      str(self._server_port) + ', exception: ' + str(e))
