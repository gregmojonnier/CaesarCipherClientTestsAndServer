import socket
import select
import time
import pytest
import string
import os
from multiprocessing import Process, Manager


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


def test_ClientsFirstMessageHasNoTrailingSpace_ServerWillWaitForAdditionalMessages(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    one_second_timeout = 1
    timed_out = False

    sock.sendall(b'text_without_a_trailing_space')
    sock.setblocking(0)
    ready = select.select([sock], [], [], one_second_timeout)
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


def test_ClientsFirstWordIsANumberAndSecondHasTrailingSpace_ServerRespondsWithMessage(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'123 message ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response


def test_ShiftOfZero_ServerRespondsWithSecondWordUnchanged(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'0 unchanged_message ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'unchanged_message '

def test_ShiftOfOneSingleCharMessage_ServerRespondsWithCharShiftedOne(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'1 a ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'b '

def test_ShiftOfOneMultipleCharsMessage_ServerRespondsWithSecondWordsCharsShiftedOne(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'1 abc ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'bcd '


def test_ShiftOfTwoMultipleCharsMessage_ServerRespondsWithSecondWordsCharsShiftedTwo(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'2 abc ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'cde '

def test_MultipleShiftOfOneCharMessages_RespondsWithCharsShiftedOneWithTrailingSpaces(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'1 a 1 b ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'b c '

def test_ShiftOfOneWithLastAsciiCharMessage_RespondsWithFirstAsciiChar(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'1 \x7f ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == '\x00 '

def test_ShiftOfNegativeOneSingleCharMessage_ServerRespondsWithCharShiftedNegativeOne(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'-1 b ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'a '

def test_ShiftOfNegativeOneWithFirstAsciiCharMessage_RespondsWithLastAsciiChar(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'-1 \x00 ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == '\x7f '

def test_ShiftOfAsciiRange_RespondsWithSameMessage(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'128 ' + string.ascii_lowercase + ' ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == string.ascii_lowercase + ' '

def test_ShiftOfAsciiRangePlusOne_RespondsWithTheMessagePlusOne(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None

    try:
        sock.sendall(b'129 ' + string.ascii_lowercase + ' ')
        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'bcdefghijklmnopqrstuvwxyz{ '

def test_ShiftAndMessageSentOneCharAtATime_RespondsCorrectly(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    response = None
    message = 'abcd'
    shift = str((128 * 3) + 1) # shift 1

    try:
        for digit in shift:
            sock.sendall(digit.encode())
        sock.sendall(' '.encode())

        for char in message:
            sock.sendall(char.encode())
        sock.sendall(' '.encode())

        response = sock.recv(1024)
    except socket.error, e:
        pass

    assert response == 'bcde '

@pytest.mark.skip()
def test_ExtremelyLargeMessageContainingMultipleRequests_RespondsCorrectly(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    message = ''
    response = ''
    expected_response = ''

    for idx in range(30000):
        message +=  '129 ' + string.ascii_lowercase + ' '
        expected_response += string.ascii_lowercase[1:] + '{ '

    try:
        sock.sendall(message.encode())
        
        while True:
            partial_response = sock.recv(1024)
            if not partial_response:
                break
            response += partial_response

    except socket.error, e:
        pass

    assert response == expected_response

@pytest.mark.skip()
@pytest.mark.timeout(15)
def test_ExtremelyLargeMessageContainingMultipleRequests_RespondsInATimelyManner(CaesarCipherServerFixture):
    sock = CaesarCipherServerFixture._sock
    message = ''
    response = ''
    expected_response = ''

    for idx in range(30000):
        message +=  '129 ' + string.ascii_lowercase + ' '
        expected_response += string.ascii_lowercase[1:] + '{ '

    try:
        sock.sendall(message.encode())

        while True:
            partial_response = sock.recv(1024)
            if not partial_response:
                break
            response += partial_response
    except socket.error, e:
        pass

def NewProcessCipherRequester(request_message, result):
    """Function to be run in a new process that
       connects to server and sends request_message
       storing the pid -> answer in result. """

    _host = '127.0.0.1'
    _server_port = 55555
    sock = None
    response = ''

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((_host, _server_port))

        sock.sendall(request_message.encode())
        sock.sendall(b'')
        result[os.getpid()] = sock.recv(1024)
    except Exception:
        pass
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()

def test_MultipleClientsConcurrently_RespondsToAllCorrectly(CaesarCipherServerFixture):
    manager = Manager()
    shared_dict = manager.dict()
    total_clients = 6
    clients = []

    shift_one_alphabet_request = '1 ' + string.ascii_lowercase + ' '
    expected_result = string.ascii_lowercase[1:] + '{ '

    for i in range(total_clients):
        clients.append(Process(target=NewProcessCipherRequester, args=(shift_one_alphabet_request, shared_dict,)))

    for client in clients:
        client.start()

    for client in clients:
        client.join(10)
        if client.is_alive():
            client.terminate()

    assert len(shared_dict) == total_clients, 'Did not get an answer from all concurrent clients'

    for pid, pids_result in shared_dict.items():
        assert pids_result == expected_result, 'Process ' + str(pid) + '\'s ciphered message was incorrect.'
