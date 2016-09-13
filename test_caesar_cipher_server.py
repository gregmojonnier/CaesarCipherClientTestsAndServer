import socket
import select
import time
import pytest


@pytest.fixture
def CaesarCipherServerFixture(request):
    class TestInfo:
        _host = '127.0.0.1'
        _server_port = 55555
        _sock = None

        def __init__(self):
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self._sock.connect((self._host, self._server_port))
            except Exception as e:
                assert False, 'Unable to connect to server on port ' + \
                    str(self._server_port) + ', exception: ' + str(e)

    t = TestInfo()

    def Uninitialize():
        t._sock.shutdown(socket.SHUT_RDWR)
        t._sock.close()
        t._sock = None

    request.addfinalizer(Uninitialize)
    return t


def test_ClientSendsTextWithosdfutTrailingSpace_ServerWillWaitForAdditionalMessages(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    two_second_timeout = 2
    timed_out = False

    sock.sendall(b'text_without_a_trailing_space')
    sock.setblocking(0)
    ready = select.select([sock], [], [], two_second_timeout)
    if not ready[0]:
        timed_out = True

    assert timed_out


def test_ClientsFirstWordIsNotANumber_ServerClosesConnection(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'Not_A_Number message')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == ''


def test_ClientsFirstWordIsANumber_ServerRespondsWithMessage(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'32 message')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response
