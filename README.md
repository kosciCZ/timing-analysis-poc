Timing analysis proof-of-concept (tapoc)
================================
This package exists to figure out, how to do timing analysis in python. 
Outputs of this work will be later turned into a part of [tlsfuzzer](https://github.com/tomato42/tlsfuzzer) to extend it's ability to test TLS implementations.

## Concept
The general idea of timing analysis is to try and estimate how long operation on server took and exploit this knowledge.
The process as implemented here can be divided into three phases:
1. Collection
   - Client repeatedly sends queries to which server replies, depending on the query.
   - `tcpdump` is running in a subprocess, capturing the traffic
2. Extraction
   - The process of gathering timing information from the pcap file and assigning that information to it's respective query
3. Analysis
   - Because network introduces noise to the timing information, data can't be taken as they are
   - Therefore, some kind of statistical testing is needed in order to be able to tell if two queries differ in timing or not

## Repository overview
In this repository you can find the client-server application itself, 
and then some code in R that can be used for statistical testing and visualisation. 

## Server
Server is able to recieve and answer following queries:

| Name       | Binary       | Answer binary |
|:----------:|:------------:|:-------------:|
| GOOD       | `00`         | `0`           |
| BAD        | `01`         | `1`           |
| BAAD       | `11`         | `1`           |

Server simulates a timing side channel by executing `time.sleep()` for a specified time (defaults to 1ms) before replying in case of BAAD query.
This is mean to create difference between BAD and BAAD query, where the reply is the same, but timing is different.
See usage for options.

## Client
Client's purpose is to send queries to the server and measure the timing information. This is currently done with `tcpdump` running in a subprocess.
For less noisy results, the capturing process should have a dedicated CPU core. 
For information on how to isolate cores in linux see [Hubert Kario's article](https://securitypitfalls.wordpress.com/2018/08/03/constant-time-compare-in-python/) 
and [PyPerf's page](https://pyperf.readthedocs.io/en/latest/system.html) on how to reduce noise in the system. 
Client first performs the capturing, then extracts timestamps from the packet capture and outputs them into a csv file. 
It has two modes of running, the regular mode, which sends specified amount of each query (GOOD, BAD, BAAD in this order) and sanity mode,
which is used for checking if measurements of GOOD query are consistent over time. 
No matter the mode, client sends a specified amount of queries at the start, to get to a more consistent state (e.g. fill up system's caches).
CSV produced at the end has timing information for each query in each row. Client can be configured via these options:
See usage for options.

## Parser 
Because sometimes you might want to process the capture file elsewhere than on the capturing device (think Raspberry Pi), there's a Parser module available.
It's job is to extract timing information, assign it to the correct query and to dump it into a csv. See usage for options.

## Usage
This package contains three available commands, that reflect the previous sections:
```
tapoc [-h] {server,client,parse}
```
Here are the options for the server:

| Option                       | Description       | Required      |
|------------------------------|-------------------|---------------|
| `--ip` | IP address the server should run on. Defaults to `127.0.0.1`| No |
| `--port` | Port the server should run on. Defaults to `20300` | No|
| `--sleep` | For how many seconds should server sleep on BAAD query. Can be a float. Defaults to `0.001` | No |

And for the client:

| Option                       | Description       | Required      |
|------------------------------|-------------------|---------------|
| `--server-ip` | Server's IP address. Defaults to `127.0.0.1` | No|
| `--server-port` | Server's port. Defaults to `20300` | No |
| `--repetitions` | How many times to repeat each query. Defaults to `10000`| No|
| `--interface` | On which interface should `tcpdump` be capturing. Defaults to `lo` | No |
| `--warmup` | How many queries to send at the start to get to consistent state. Defaults to `500` | No |
| `--cooldown` | How many seconds to wait before sending each query. Can be a float. Defaults to `0.001` | No |
| `--cpu` | Which cpu should `tcpdump` run on (uses `taskset --cpu-list`) | No |
| `--sanity-check` | Enables sanity check mode. Defaults to `False`| No |
| `--capture-only` | Only produces a capture file, doesn't do extraction. Defaults to `False` | No |

And for the parser:

| Option                       | Description       | Required      |
|------------------------------|-------------------|---------------|
| `--input` | Input pcap file. | Yes |
| `--server-ip` | IP address the server was running on. Defaults to `127.0.0.1`| No |
| `--server-port` | Port the server was running on. Defaults to `20300` | No|
| `--repetitions` | How many times each query was repeated. Defaults to `10000`| No|
| `--warmup` | How many queries were sent as a warmup. Defaults to `500` | No |
| `--queries` | Queries in their byte representation (eg. 0001 for 00 and 01) | No |
| `--log`   | Log file from Client to read configuration from. If specified, other options except `--input` are ignored | No|
