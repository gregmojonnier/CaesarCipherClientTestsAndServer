import socket
import select
import enum
import argparse
from caesar_cipher import GenerateCaesarCipher

class CaesarCipherServer:
    '''Caesar cipher socket server. Handles incoming requests to
    encode ASCII messages using a user specified shift.
    Returns an encoded caesar cipher to the user.
    '''


    def __init__(self, port):
        self._port = port

    def run(self):
        '''Starts the server on the port specified in the constructor.'''
        self._sock = self._create_port_listener()
        while True:
            (conn, addr) = self._sock.accept()
            conn.setblocking(0)
            self._handle_incoming_connection(conn, addr)

    def _create_port_listener(self):
        '''Creates a listening socket bound to localhost.'''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        HOST = ''
        s.bind((HOST, self._port))
        s.listen(5)
        return s

    class AwaitingState(enum.Enum):
        '''Tracks the state of how the server will interpret the incoming contiguous segment of text.'''
        ShiftAmount = 1
        Message = 2

    def _handle_incoming_connection(self, conn, addr):
        '''Handles parsing and responding to a connection's incoming caesar cipher encodings requests.
        Expected Incoming Message Format:
            "shift message "
        A space signifies completion of a shift or message word. Spaces are not allowed in messages.

        Expected Outgoing Message Format:
            "encoded_message "
        A trailing space is sent with the encoded_message.
        '''

        try:
            print('connection from ', addr)
            waiting_for = self.AwaitingState(self.AwaitingState.ShiftAmount)
            complete_ciphers_to_send = []
            shift_amount = 0
            incomplete_shift_amount = ''
            incomplete_message = ''
            while True:
                try:
                    full_data_string = self._wait_for_data_string(conn)
                except TimeoutError as e:
                    print(e)
                    return
                except ConnectionAbortedError as e:
                    print(e)
                    return

                print('incoming message ', full_data_string, '\n')

                split_words = full_data_string.split(' ')
                num_words = len(split_words)
                print('split incoming message ', split_words, '\n')

                for idx, word in enumerate(split_words):
                    word_followed_by_space = idx < num_words-1
                    if waiting_for == self.AwaitingState.ShiftAmount:
                        incomplete_shift_amount += word
                        if word_followed_by_space:
                            is_negative = incomplete_shift_amount.startswith('-')

                            if not is_negative:
                                if not incomplete_shift_amount.isnumeric():
                                    print('not numeric number given\n')
                                    conn.shutdown(socket.SHUT_RDWR)
                                    break
                                shift_amount = int(incomplete_shift_amount)
                            else:
                                number_portion = incomplete_shift_amount[1:]
                                if not number_portion.isnumeric():
                                    print('not numeric number given\n')
                                    conn.shutdown(socket.SHUT_RDWR)
                                    break
                                shift_amount = -int(number_portion)

                            print('shift amount received', shift_amount)

                            waiting_for = self.AwaitingState.Message
                    elif waiting_for == self.AwaitingState.Message:
                        incomplete_message += word

                        if word_followed_by_space:
                            print('entire message received', incomplete_message)
                            complete_ciphers_to_send.append(GenerateCaesarCipher(incomplete_message, shift_amount))
                            print('recorded cipher, total', complete_ciphers_to_send)

                            waiting_for = self.AwaitingState.ShiftAmount
                            shift_amount = 0
                            # reset waits
                            incomplete_shift_amount = ''
                            incomplete_message = ''

                full_response_message = ''
                for cipher in complete_ciphers_to_send:
                    full_response_message += cipher + ' '
                    print('appended to full message string, total', full_response_message)

                if full_response_message:
                    print('sending full message')
                    conn.sendall(full_response_message.encode())
                    complete_ciphers_to_send = []

        except socket.timeout:
            print('Timed out')
        except Exception as e:
            print(e)
        finally:
            if conn:
                conn.close()
                print('closed connection')

    def _wait_for_data_string(self, conn):
        inputs = [conn]
        for read_attempt in range(0, 2):
            readable, writable, exceptional = select.select(inputs, [], [], 1)
            if not readable:
                if read_attempt >= 1:
                    raise TimeoutError('No messages for 2 seconds.')
            else:
                data = conn.recv(1024)
                if not data:
                    # no such thing as empty message peer disconnected
                    raise ConnectionAbortedError('Peer disconnected.')

                return data.decode()
        return ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port')
    args = parser.parse_args()

    server = CaesarCipherServer(int(args.port))
    server.run()
