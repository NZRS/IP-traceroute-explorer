from bottle import route, run, template
import json
from ripe.atlas.sagan import TracerouteResult
import networkx as nx
import requests
import sys
from collections import defaultdict
import math

stat_ripe = "https://stat.ripe.net/data/routing-status/data.json"

addr2as = {}
with open('as_map.json') as f:
    addr2as = json.load(f)


def get_addr_as(a):
    if a in addr2as:
        return addr2as[a]

    r = requests.get(stat_ripe, params={'resource': a})
    response = r.json()

    origin = set()
    try:
        origin = set([o['origin'] for o in response['data']['origins']])
    except KeyError:
        return None

    return list(origin)[0]


def transform_graph(g):
    nl = []
    n_idx = {}
    for n in g.nodes_iter():
        idx = g.node[n]['index']
        nl.append({'label': n, 'id': idx, 'value': g.node[n]['hops']})
        n_idx[n] = idx

    el = [{'to': n_idx[t],
           'from': n_idx[s],
           'value': math.sqrt(d['rtt']),
           'label': d['rtt']} for s, t, d in g.edges_iter(data=True)]

    return nl, el


@route('/path/<family>')
def index(family):
    if family == 'ipv4':
        msm_file = '3806401.json'
    elif family == 'ipv6':
        msm_file = '3806402.json'

    # Read the data
    G = nx.DiGraph()
    hop_cnt = defaultdict(int)
    hop_idx = defaultdict(int)
    with open(msm_file) as f:
        res_blob = json.load(f)

        seq = []
        for res_set in res_blob:
            sagan_res = TracerouteResult(res_set)

            asn = get_addr_as(sagan_res.origin)
            prev_asn = asn
            hop_cnt[asn] += 1
            for hop in sagan_res.hops:
                hop_addr = set()
                for packet in hop.packets:
                    if packet.origin is None:
                        continue

                    hop_addr.add(packet.origin)

                for a in hop_addr:
                    asn = get_addr_as(a)
                    hop_cnt[asn] += 1
                    hop_idx[asn] = hop.index
                    addr2as[a] = asn
                    if prev_asn != asn:
                        G.add_edge(prev_asn, asn, rtt=hop.median_rtt)
                        prev_asn = asn

    for n in G.nodes_iter():
        G.node[n]['hops'] = hop_cnt[n]
        G.node[n]['index'] = hop_idx[n]

    n, e = transform_graph(G)

    # Return an object
    return {'nodes': n, 'edges': e}

run(host='localhost', port=8080)
