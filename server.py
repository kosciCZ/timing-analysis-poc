import socket
import argparse
import time


class Server:

    def __init__(self, ip, port, sleep):
        self.ip = ip
        self.port = port
        self.sleep = sleep

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.ip, self.port))
        sock.listen()

        while True:
            conn, addr = sock.accept()
            with conn:
                data = b""
                data += conn.recv(2)
                if len(data) == 2:
                    response = self.decide_response(data)
                elif len(data) == 1:
                    data += conn.recv(1)
                    response = self.decide_response(data)
                else:
                    break
                conn.sendall(response)
                data = b""
                conn.close()

    def decide_response(self, incoming_data):
        response = b"0"
        # GOOD
        if incoming_data == b"00":
            pass
        # BAD
        elif incoming_data == b"01":
            response = b"1"
        # BAAD
        elif incoming_data == b"11":
            time.sleep(self.sleep)
            response = b"1"
        return response


parser = argparse.ArgumentParser(description="Timing analysis test server")
parser.add_argument('--ip', help="IP address server runs on", default="127.0.0.1")
parser.add_argument('--port', help="Port server runs on", type=int, required=True)
parser.add_argument('--sleep', help="Amount of time to sleep for BAAD queries in seconds", type=float, default=0.001)

args = parser.parse_args()
server = Server(args.ip, args.port, args.sleep)
server.run()
