import socket
import select


def CreateCaesarCipherMessage(message, shift):
    ret = ""

    for i in message:
        ret += chr(ord(i) + shift)

    return ret.encode()

def handle_connection(conn, addr):
    try:
        conn.setblocking(0)
        print('connection from ', addr)
        waiting_for_shift = True
        shift_amount = ''
        message = ''
        read_timeouts = 0
        inputs = [conn]
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

            if waiting_for_shift:
                if ' ' not in full_data_string:
                    print('waiting for a space still')
                    shift_amount += full_data_string
                    print('current shift ', shift_amount)
                    continue

                print('the split,', full_data_string.split(' '))
                remaining_shift_data = full_data_string.split(' ')[0]
                shift_amount += remaining_shift_data

                split_words = full_data_string.split(' ')
                num_words = len(split_words)
                if num_words > 1:
                    message += split_words[1]
                    if num_words > 2:
                        # end of message
                        res = CreateCaesarCipherMessage(message, int(shift_amount))
                        conn.sendall(res)
                        # todo handle remainder

                print('parsed messae so far', message)

                if shift_amount.isnumeric():
                    waiting_for_shift = False
                else:
                    print('not numeric number given\n')
                    conn.shutdown(socket.SHUT_RDWR)
                    break
            else:
                print('process message\n')
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
