import csv
import dpkt
from decimal import *
from socket import inet_aton


class Parse:
    def __init__(self, ip, port, repetitions, input_file):
        self.server_ip = inet_aton(ip)
        self.server_port = port
        self.repetitions = repetitions
        self.input_file = input_file
        self.times = []
        self.query_time_capture = Decimal(0)
        self.ip = ''
        self.port = 0

    def get_times(self):
        with open(self.input_file, 'rb') as file:
            pcap = dpkt.pcap.Reader(file)

            for timestamp, pkt in pcap:
                eth = dpkt.ethernet.Ethernet(pkt)
                ip = eth.data
                tcp = ip.data

                # save source ip and port if you detect a new connection opening to the server
                if (tcp.flags & dpkt.tcp.TH_SYN) \
                        and tcp.dport == self.server_port \
                        and ip.dst == self.server_ip:
                    self.ip = ip.src
                    self.port = tcp.sport

                # only interested in payload packets
                if not tcp.data:
                    continue

                ts = Decimal(str(timestamp))
                # is it a client query?
                if ip.src == self.ip and tcp.sport == self.port:
                    self.query_time_capture = ts
                # a server response
                else:
                    self.times.append(str(ts - self.query_time_capture))

    def dump_csv(self, filename, warmup):
        good_data = self.times[warmup:self.repetitions + warmup]
        bad_data = self.times[self.repetitions + warmup:2 * self.repetitions + warmup]
        baad_data = self.times[2 * self.repetitions + warmup:3 * self.repetitions + warmup]
        with open(f'{filename}.csv', 'w') as csvfile:
            print(f"Writing to {filename}.csv")
            writer = csv.writer(csvfile,
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(good_data)
            writer.writerow(bad_data)
            writer.writerow(baad_data)

