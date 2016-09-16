import socket
import select
import enum

LAST_ASCII_CHAR = 127
FIRST_ASCII_CHAR = 0
def CreateCaesarCipherMessage(message, shift):
    ret = ""

    for i in message:
        print("cur", ord(i))
        future_value = ord(i) + shift
        print("future ", future_value)

        if future_value > LAST_ASCII_CHAR:
            future_value = (future_value - LAST_ASCII_CHAR) - 1
            print("adjusted future ", future_value)
        elif future_value < FIRST_ASCII_CHAR:
            future_value = (future_value + LAST_ASCII_CHAR) + 1
            print("adjusted future ", future_value)

        ret += chr(future_value)

    return ret

class AwaitingState(enum.Enum):
    ShiftAmount = 1
    Message = 2
    


def handle_connection(conn, addr):
    try:
        conn.setblocking(0)
        print('connection from ', addr)
        waiting_for_shift = True
        message = ''
        read_timeouts = 0
        inputs = [conn]

        waiting_for = AwaitingState(AwaitingState.ShiftAmount)
        incomplete_shift_amount = ''
        incomplete_message = ''
        while True:
            print('about to select')
            readable, writable, exceptional = select.select(inputs, [], [], 2)
            if not readable:
                if read_timeouts < 2:
                    print('timeout num ', read_timeouts)
                    read_timeouts += 1
                    continue
                else:
                    print('out of timeouts')
                    return
            else:
                print('was ready')

            data = conn.recv(1024)
            if not data:
                print('no data, returning')
                # no such thing as empty message peer disconnected
                return

            full_data_string = data.decode()
            print('full msg', full_data_string, '\n')

            split_words = full_data_string.split(' ')
            num_words = len(split_words)
            print('split message ', split_words, '\n')

            complete_ciphers_to_send = []
            shift_amount = 0
            for idx, word in enumerate(split_words):
                word_followed_by_space = idx < num_words-1
                if waiting_for == AwaitingState.ShiftAmount:
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
                        
                        waiting_for = AwaitingState.Message
                elif waiting_for == AwaitingState.Message:
                    incomplete_message += word

                    if word_followed_by_space:
                        complete_ciphers_to_send.append(CreateCaesarCipherMessage(incomplete_message, shift_amount))
                        print('recorded cipher, total', complete_ciphers_to_send)

                        waiting_for = AwaitingState.ShiftAmount
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

    except socket.timeout:
        print('Timed out')
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()
            print('closed connection')


def start():
    HOST = ''
    PORT = 55555

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        print('about to accept, listening on', PORT)
        (conn, addr) = s.accept()
        handle_connection(conn, addr)


if __name__ == '__main__':
    start()
