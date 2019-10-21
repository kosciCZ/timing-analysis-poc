import csv
import dpkt
from decimal import *
from socket import inet_aton
from .util import GOOD, BAD, BAAD


class Parse:
    def __init__(self, ip, port, repetitions, input_file, warmup, queries, sanity_check=False):
        self.server_ip = inet_aton(ip)
        self.server_port = port
        self.repetitions = repetitions
        self.warmup = warmup
        self.input_file = input_file
        self.times = [[] for _ in queries]
        self.query_time_capture = Decimal(0)
        self.ip = ''
        self.sanity_check = sanity_check
        self.port = 0
        self.queries = queries

    def get_times(self):
        with open(self.input_file, 'rb') as file:
            pcap = dpkt.pcap.Reader(file)

            counter = 0
            query = 0
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
                    if counter >= 500:
                        if self.queries[query] != tcp.data:
                            print(f"Query mismatch {self.queries[query]} vs {tcp.data}")
                # a server response
                else:
                    # if it is warmup, just skip it
                    if counter < self.warmup:
                        counter += 1
                        continue
                    self.times[query].append(str(ts - self.query_time_capture))
                    query = (query + 1) % len(self.queries)

    def dump_csv(self, filename):
        data = self.times
        if not self.sanity_check:
            good_data = self.times[self.queries.index(GOOD)]
            bad_data = self.times[self.queries.index(BAD)]
            baad_data = self.times[self.queries.index(BAAD)]
            data = [good_data, bad_data, baad_data]
        with open(f'{filename}.csv', 'w') as csvfile:
            print(f"Writing to {filename}.csv")
            writer = csv.writer(csvfile,
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in data:
                writer.writerow(row)
