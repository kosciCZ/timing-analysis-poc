import socket
import argparse
import time
import subprocess
import os
import csv
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, defragment


class Test:

    def __init__(self, sever_ip, server_port, repetitions, interface, ip=None, port=None):
        self.server_ip = sever_ip
        self.server_port = server_port
        self.repetitions = repetitions
        self.interface = interface

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
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # start sniffing
        sniffer = self.sniff(f'host {self.server_ip} and port {self.server_port} and tcp')
        print(f'host {self.server_ip} and port {self.server_port} and tcp')

        # sleep for a second to give tcpdump time to start capturing
        time.sleep(2)

        sock.connect((self.server_ip, self.server_port))
        self.ip, self.port = sock.getsockname()
        print(f'Assigned ip:port - {self.ip}:{self.port}')
        queries = [self.good_query, self.bad_query, self.baad_query]
        for query in queries:
            print(f"Sending {self.repetitions}x query {query}")
            for i in range(0, self.repetitions):
                sock.sendall(query)
                data = sock.recv(1)
        sock.close()

        # stop sniffing and give tcpdump time to write all buffered packets
        time.sleep(2)
        sniffer.terminate()

    def sniff(self, packet_filter=''):
        flags = ['-i', 'lo', '-U', '-nn', '--time-stamp-precision', 'nano']
        output_file = os.path.join(os.getcwd(), f'{self.output}.pcap')
        return subprocess.Popen(['tcpdump', packet_filter, '-w', output_file] + flags)

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
            # only interested in packets with payload and those that are not duplicates on loopback
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Timing analysis test client")
    parser.add_argument('--server-ip', help="Server IP address", dest='ip', default='127.0.0.1')
    parser.add_argument('--server-port', help="Server port", dest='port', type=int, default=20300)
    parser.add_argument('--repeat', help="How many times each query should be repeated", type=int, default=100)
    parser.add_argument('--interface', help="Network interface to sniff on", default='lo')
    args = parser.parse_args()
    test = Test(args.ip, args.port, args.repeat, args.interface)
    test.run()
    times = test.get_times(f'{test.output}.pcap')

    for kind in ['capture', 'timestamp']:
        times[kind] = [str(x) for x in times[kind]]
        good_data = times[kind][0:test.repetitions]
        bad_data = times[kind][test.repetitions:2 * test.repetitions]
        baad_data = times[kind][2 * test.repetitions:3 * test.repetitions]
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
