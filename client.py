import socket
import argparse
import time
import subprocess
import os
import csv
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, defragment


class Test:

    def __init__(self, sever_ip, server_port, repetitions, interface, warmup, sanity_check, cooldown, ip=None,
                 port=None):
        self.server_ip = sever_ip
        self.server_port = server_port
        self.repetitions = repetitions
        self.interface = interface

        self.warmup = warmup
        self.cooldown = cooldown
        self.sanity_check = sanity_check

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

        # output a short log with info about this run
        with open(f"{self.output}_log.txt", 'w') as log:
            log.write(f"server: {self.server_ip}:{self.server_port}\n")
            log.write(f"repetitions: {self.repetitions}\n")
            log.write(f"warmup: {self.warmup}\n")
            log.write("queries:\n")
            log.writelines([f"{x.decode()}\n" for x in queries])

    def conversation(self, query, repetitions=1):
        for i in range(0, repetitions):
            time.sleep(self.cooldown)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_ip, self.server_port))
            self.ip, self.port = sock.getsockname()
            sock.sendall(query)
            data = sock.recv(1)

    def sniff(self, packet_filter=''):
        flags = ['-i', 'lo', '-U', '-nn', '--time-stamp-precision', 'nano']
        output_file = os.path.join(os.getcwd(), f'{self.output}.pcap')
        return subprocess.Popen(['taskset', '1', 'tcpdump', packet_filter, '-w', output_file] + flags)

    def get_times(self, capture):
        packets = rdpcap(capture)
        packets = defragment(packets)
        times = {'timestamp': [], 'capture': []}
        query_time_capture = 0.0
        query_time_timestamp = 0

        for packet in packets:
            ip_pkt = packet[IP]
            tcp_pkt = packet[TCP]

            src_ip = ip_pkt.fields['src']
            src_port = tcp_pkt.fields['sport']

            # save source ip and port if you detect a new connection opening to the server
            if is_syn(tcp_pkt) \
                    and tcp_pkt.fields['dport'] == self.server_port \
                    and ip_pkt.fields['dst'] == self.server_ip:
                self.ip = src_ip
                self.port = src_port

            # only interested in packets with payload
            if not tcp_pkt.payload:
                continue

            # is it a client query?
            if src_ip == self.ip and src_port == self.port:
                query_time_capture = packet.time
                # save TSecr
                _, query_time_timestamp = get_timestamp(tcp_pkt)
            # a server response
            else:
                times['capture'].append(packet.time - query_time_capture)
                tsval, _ = get_timestamp(tcp_pkt)
                if query_time_timestamp and tsval:
                    times['timestamp'].append(tsval - query_time_timestamp)
        return times


def get_timestamp(tcp_packet):
    options = tcp_packet.fields.get('options')
    if options:
        for (option, value) in options:
            if option == 'Timestamp':
                tsval, tsecr = value
                return tsval, tsecr
    return None, None


def is_syn(tcp_packet):
    return tcp_packet.flags & 0x02


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Timing analysis test client")
    parser.add_argument('--server-ip', help="Server IP address", dest='ip', default='127.0.0.1')
    parser.add_argument('--server-port', help="Server port", dest='port', type=int, default=20300)
    parser.add_argument('--repeat', help="How many times each query should be repeated", type=int, default=100)
    parser.add_argument('--interface', help="Network interface to sniff on", default='lo')
    parser.add_argument('--warmup', help="How many conversations to have to get system to reproducible state", type=int,
                        default=500)
    parser.add_argument('--cooldown', help="How long to wait before each conversation", type=float, default=0.002)
    parser.add_argument('--sanity-check', help='Sends only GOOD queries', dest='sanity_check',
                        action='store_true', default=False)
    args = parser.parse_args()
    test = Test(args.ip, args.port, args.repeat, args.interface, args.warmup, args.sanity_check, args.cooldown)
    test.run()
    times = test.get_times(f'{test.output}.pcap')

    for kind in ['capture', 'timestamp']:
        times[kind] = [str(x) for x in times[kind]]
        good_data = times[kind][test.warmup:test.repetitions + test.warmup]
        bad_data = times[kind][test.repetitions + test.warmup:2 * test.repetitions + test.warmup]
        baad_data = times[kind][2 * test.repetitions + test.warmup:3 * test.repetitions + test.warmup]
        with open(f'{test.output}_{kind}.csv', 'w') as csvfile:
            print(f"Writing to {test.output}_{kind}.csv")
            writer = csv.writer(csvfile,
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(good_data)
            writer.writerow(bad_data)
            writer.writerow(baad_data)

    # call R script for analysis
    result = subprocess.run(['Rscript', 'analysis.r', test.output], stdout=subprocess.PIPE, universal_newlines=True)
    if result.stdout:
        print(result.stdout)
