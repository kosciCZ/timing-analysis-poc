import socket
import argparse
import time


def run(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen()

    while True:
        conn, addr = sock.accept()
        try:
            data = b""
            while True:
                data += conn.recv(2)
                if len(data) == 2:
                    response = decide_response(data)
                elif len(data) == 1:
                    data += conn.recv(1)
                    response = decide_response(data)
                else:
                    break
                conn.sendall(response)
                data = b""
        finally:
            conn.close()


def decide_response(incoming_data):
    response = b"0"
    # GOOD
    if incoming_data == b"00":
        print("GOOD")
    # BAD
    elif incoming_data == b"01":
        response = b"1"
        print("BAD")
    # BAAD
    elif incoming_data == b"11":
        time.sleep(0.001)
        print("BAAD")
        response = b"1"
    return response


parser = argparse.ArgumentParser(description="Timing analysis test server")
parser.add_argument('--ip', help="IP address server runs on", default="127.0.0.1")
parser.add_argument('--port', help="Port server runs on", type=int, required=True)

args = parser.parse_args()
run(args.ip, args.port)
