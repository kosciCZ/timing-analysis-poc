import socket
import time
import subprocess
import os
import gc


class Client:

    def __init__(self, sever_ip, server_port, repetitions, interface, warmup, sanity_check, cooldown, cpu, ip=None,
                 port=None):
        self.server_ip = sever_ip
        self.server_port = server_port
        self.repetitions = repetitions
        self.interface = interface

        self.warmup = warmup
        self.cooldown = cooldown
        self.sanity_check = sanity_check
        self.cpu = cpu

        self.ip = ip
        self.port = port

        self.output = None

        # constants
        self.good_query = b"00"
        self.bad_query = b"01"
        self.baad_query = b"11"

    def run(self):
        if os.geteuid() != 0:
            print('Please run this test with root privileges, as it requires packet capturing to work.')
            raise SystemExit

        self.output = f'packets_{int(time.time())}'

        # disable garbage collection
        gc.disable()

        # start sniffing
        sniffer = self.sniff(f'host {self.server_ip} and port {self.server_port} and tcp')
        print(f'host {self.server_ip} and port {self.server_port} and tcp')

        # sleep for a second to give tcpdump time to start capturing
        time.sleep(2)

        # warm up by sending 500 packets
        self.conversation(self.good_query, self.warmup)

        # perform the actual test
        queries = [self.good_query, self.bad_query, self.baad_query]
        if self.sanity_check:
            queries = [self.good_query, self.good_query, self.good_query]
        for query in queries:
            self.conversation(query, self.repetitions)

        # stop sniffing and give tcpdump time to write all buffered packets
        time.sleep(2)
        sniffer.terminate()
        sniffer.wait()
        # enable garbage collection
        gc.enable()

        # output a short log with info about this run
        with open(f"{self.output}_log.txt", 'w') as log:
            log.write(f"server: {self.server_ip}:{self.server_port}\n")
            log.write(f"repetitions: {self.repetitions}\n")
            log.write(f"warmup: {self.warmup}\n")
            log.write(f"cooldown: {self.cooldown}\n")
            log.write(f"cpu isolation: {self.cpu}\n")
            log.write("queries:\n")
            log.writelines([f"{x.decode()}\n" for x in queries])

    def conversation(self, query, repetitions=1):
        for _ in range(0, repetitions):
            time.sleep(self.cooldown)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((self.server_ip, self.server_port))
            self.ip, self.port = sock.getsockname()
            sock.sendall(query)
            data = sock.recv(1)

    def sniff(self, packet_filter=''):
        flags = ['-i', self.interface, '-U', '-nn', '--time-stamp-precision', 'nano']
        output_file = os.path.join(os.getcwd(), f'{self.output}.pcap')
        cpu_affinity = ['taskset', '--cpu-list', str(self.cpu)] if self.cpu else []
        return subprocess.Popen(cpu_affinity + ['tcpdump', packet_filter, '-w', output_file] + flags)
