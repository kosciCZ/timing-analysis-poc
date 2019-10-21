import socket
import time
from .util import GOOD, BAD, BAAD

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
            conn, _ = sock.accept()
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
        if incoming_data == GOOD:
            pass
        elif incoming_data == BAD:
            response = b"1"
        elif incoming_data == BAAD:
            time.sleep(self.sleep)
            response = b"1"
        return response
