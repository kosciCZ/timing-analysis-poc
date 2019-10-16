import argparse
from .server import Server
from .client import Client
from .parse import Parse

DEFAULTS = {
    'server_ip': '127.0.0.1',
    'server_port': 20300,
    'repetitions': 10000,
    'warmup': 500
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Timing Analysis Proof-Of-Concept", prog="tapoc")
    sub = parser.add_subparsers(dest='cmd')

    # server command
    parser_server = sub.add_parser('server', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_server.add_argument('--ip', help="IP address server runs on",
                               default=DEFAULTS['server_ip'])
    parser_server.add_argument('--port', help="Port server runs on", type=int,
                               default=DEFAULTS['server_port'])
    parser_server.add_argument('--sleep',
                               help="Amount of time to sleep for BAAD queries in seconds",
                               type=float,
                               default=0.001)

    # client command
    parser_client = sub.add_parser('client', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_client.add_argument('--server-ip', help="Server IP address", dest='ip',
                               default=DEFAULTS['server_ip'])
    parser_client.add_argument('--server-port', help="Server port", dest='port', type=int,
                               default=DEFAULTS['server_port'])
    parser_client.add_argument('--repetitions', help="How many times each query should be repeated",
                               dest="repeat",
                               type=int, default=DEFAULTS['repetitions'])
    parser_client.add_argument('--interface', help="Network interface to sniff on", default='lo')
    parser_client.add_argument('--warmup',
                               help="How many conversations to have to get system to reproducible state ",
                               type=int,
                               default=DEFAULTS['warmup'])
    parser_client.add_argument('--cooldown', help="How long to wait before each conversation",
                               type=float,
                               default=0.003)
    parser_client.add_argument('--cpu',
                               help="Id of isolated cpu for packet capture (uses taskset --cpu-list)",
                               type=int)
    parser_client.add_argument('--sanity-check', help='Sends only GOOD queries',
                               dest='sanity_check',
                               action='store_true', default=False)
    parser_client.add_argument('--capture-only', help='Only produces log and pcap file',
                               dest='capture_only',
                               action='store_true', default=False)

    # parse command
    parser_parse = sub.add_parser('parse', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_parse.add_argument('--server-ip', help="Server IP address", dest='ip',
                              default=DEFAULTS['server_ip'])
    parser_parse.add_argument('--server-port', help="Server port", dest='port', type=int,
                              default=DEFAULTS['server_port'])
    parser_parse.add_argument('--input', help='Input pcap file', dest='input', required=True)
    parser_parse.add_argument('--repetitions', help='Repetitions of each query', dest='repeat',
                              type=int,
                              default=DEFAULTS['repetitions'])
    parser_parse.add_argument('--warmup', help='How many warmup conversations', dest='warmup',
                              type=int,
                              default=DEFAULTS['warmup'])

    args = parser.parse_args()

    if args.cmd == "server":
        server = Server(args.ip, args.port, args.sleep)
        server.run()
    elif args.cmd == "client":
        test = Client(args.ip, args.port, args.repeat, args.interface, args.warmup,
                      args.sanity_check, args.cooldown,
                      args.cpu)
        test.run()
        if not args.capture_only:
            parse = Parse(args.ip, args.port, args.repeat, f'{test.output}.pcap')
            parse.get_times()
            parse.dump_csv(test.output, args.warmup)
    elif args.cmd == "parse":
        t = Parse(args.ip, args.port, args.repeat, args.input)
        output = args.input
        if args.input[-5:] == ".pcap":
            output = args.input[:-5]
        t.get_times()
        t.dump_csv(output, args.warmup)
