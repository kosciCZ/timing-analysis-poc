import json
import argparse

GOOD = b"00"
BAD = b"01"
BAAD = b"11"


def parse_log(file):
    with open(file, 'r') as fd:
        log = json.load(fd)
        log['queries'] = [bytes(query, 'utf-8') for query in log['queries']]
    return log


def queries(q):
    if len(q) % 2 != 0:
        raise argparse.ArgumentTypeError("Each query must be two bits long")

    queries = []
    query = ""
    counter = 0
    for c in q:
        if counter % 2 == 0:
            query = c
        else:
            queries.append(bytes(f"{query}{c}", 'utf-8'))
            query = ""
        counter += 1

    return queries
