import socket
import select
import unittest
import time


class CaesarCipherServerTests(unittest.TestCase):
    _host = '127.0.0.1'
    _server_port = 55555
    _sock = None

    def setUp(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def tearDown(self):
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()
        self._sock = None

    def connect_to_server(self):
        try:
            self._sock.connect((self._host, self._server_port))
        except Exception as e:
            self.fail('Unable to connect to server on port ' +
                      str(self._server_port) + ', exception: ' + str(e))

    def test_ServerIsRunning_AConnectionIsEstablished(self):
        self.connect_to_server()

    def test_ClientSendsTextWithoutTrailingSpace_ServerWillWaitForAdditionalMessages(self):
        self.connect_to_server()
        two_second_timeout = 2
        timed_out = False

        self._sock.sendall(b'text_without_a_trailing_space')

        self._sock.setblocking(0)
        ready = select.select([self._sock], [], [], two_second_timeout)
        if not ready[0]:
            timed_out = True
        self.assertTrue(timed_out)

    def test_ClientsFirstWordIsNotANumber_ServerWontRespondAndClosesConnection(self):
        self.connect_to_server()
        response = None
        try:
            self._sock.sendall('Not_A_Number message'.encode())
            response = self._sock.recv(1024)
            self.assertFalse(response)
        except socket.error, e:
            self.fail(
                'Socket error ' + str(e))

    def test_ClientsFirstWordIsANumber_ServerRespondsWithNonEmptyMessageAndKeepsConnectionOpen(self):
        self.connect_to_server()
        try:
            self._sock.sendall('32 message'.encode())
            response = self._sock.recv(1024)
            self.assertTrue(response)
        except socket.error, e:
            print('sock error ', e)
            self.fail(
                'Connection was closed even though a number was sent for the first word.')
