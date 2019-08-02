import socket
import argparse
import time
import matplotlib.pyplot as plt
import numpy as np
from scapy.all import wrpcap, AsyncSniffer, rdpcap
from scapy.layers.inet import IP, TCP, defragment


class Test:

    def __init__(self, sever_ip, server_port, repetitions, interface, ip=None, port=None):
        self.server_ip = sever_ip
        self.server_port = server_port
        self.repetitions = repetitions
        self.interface = interface

        self.ip = ip
        self.port = port

        # constants
        self.good_query = b"00"
        self.bad_query = b"01"
        self.baad_query = b"11"

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # start sniffing
        sniffer = self.sniff(f'host {self.server_ip} and port {self.server_port} and tcp')
        sniffer.start()

        # sleep for a second, or Scapy won't catch all the packets
        time.sleep(1)

        sock.connect((self.server_ip, self.server_port))
        self.ip, self.port = sock.getsockname()
        queries = [self.good_query, self.bad_query, self.baad_query]
        for query in queries:
            for i in range(0, self.repetitions):
                sock.sendall(query)
                data = sock.recv(1)
                print(data)
        sock.close()

        # stop sniffing and save the capture
        sniffer.stop()
        wrpcap('packets.pcap', sniffer.results)

    def sniff(self, packet_filter=''):
        return AsyncSniffer(iface=self.interface, filter=packet_filter)

    def get_times(self, capture):
        packets = rdpcap(capture)
        packets = defragment(packets)
        useful_packets = 0
        times = {'timestamp': [], 'capture': []}
        query_time_capture = 0.0
        query_time_timestamp = 0
        for packet in packets:
            ip_pkt = packet[IP]
            tcp_pkt = packet[TCP]

            src_ip = ip_pkt.fields['src']
            src_port = tcp_pkt.fields['sport']
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


parser = argparse.ArgumentParser(description="Timing analysis test client")
parser.add_argument('--server-ip', help="Server IP address", dest='ip', default='127.0.0.1')
parser.add_argument('--server-port', help="Server port", dest='port', type=int, default=20300)
parser.add_argument('--repeat', help="How many times each query should be repeated", type=int, default=100)
parser.add_argument('--interface', help="Network interface to sniff on", required=True)
args = parser.parse_args()
test = Test(args.ip, args.port, args.repeat, args.interface)
test.run()
times = test.get_times('packets.pcap')

# plot the differences
x = t = np.arange(0, len(times['capture']), 1)
fig = plt.figure()
plt.subplot(2, 1, 1)
plt.title('Server response time')
plt.plot(x, times['timestamp'], '.-')
plt.ylabel('TCP timestamps')
plt.subplot(2, 1, 2)
plt.plot(x, times['capture'], '.-')
plt.ylabel('tcpdump timestamps')
plt.xlabel('Packet number')
plt.show()