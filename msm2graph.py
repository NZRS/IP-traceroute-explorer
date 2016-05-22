import json
from ripe.atlas.sagan import TracerouteResult
import networkx as nx
import requests
import sys
from collections import defaultdict
import math


stat_ripe = "https://stat.ripe.net/data/routing-status/data.json"
addr2as = {}


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

    if len(origin) > 0:
        return list(origin)[0]

    return None


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


with open('as_map.json') as f:
    addr2as = json.load(f)

G = defaultdict(nx.DiGraph)
hop_cnt = defaultdict(lambda: defaultdict(int))
hop_idx = defaultdict(lambda: defaultdict(int))
for msm_f in sys.argv[1:]:
    print("Parsing %s" % msm_f)
    with open(msm_f) as f:
        res_blob = json.load(f)

        seq = []
        for res_set in res_blob:
            sagan_res = TracerouteResult(res_set)

            print("AF: %s" % sagan_res.af)
            asn = get_addr_as(sagan_res.origin)
            prev_asn = asn
            hop_cnt[sagan_res.af][asn] += 1
            print("%s - %s" % (sagan_res.origin, asn))
            for hop in sagan_res.hops:
                hop_addr = set()
                for packet in hop.packets:
                    if packet.origin is None:
                        continue

                    hop_addr.add(packet.origin)

                for a in hop_addr:
                    asn = get_addr_as(a)
                    if asn is not None:
                        hop_cnt[sagan_res.af][asn] += 1
                        hop_idx[sagan_res.af][asn] = hop.index
                        addr2as[a] = asn
                    else:
                        hop_cnt[sagan_res.af][prev_asn] += 1
                        hop_idx[sagan_res.af][prev_asn] = hop.index
                        addr2as[a] = prev_asn
                    print("%s - %s [%s]" % (a, asn, hop.median_rtt))
                    if asn is not None and prev_asn != asn:
                        G[sagan_res.af].add_edge(prev_asn, asn, rtt=hop.median_rtt)
                        prev_asn = asn

for af, g in G.iteritems():
    for n in g.nodes_iter():
        g.node[n]['hops'] = hop_cnt[af][n]
        g.node[n]['index'] = hop_idx[af][n]

# with open('as_map.json', 'wb') as f:
#     json.dump(addr2as, f)

with open('graph.js', 'wb') as f:
    n, e = transform_graph(G[4])
    f.write("var src_v4_nodes = %s;\n" % json.dumps(n))
    f.write("var src_v4_edges = %s;\n" % json.dumps(e))
    n, e = transform_graph(G[6])
    f.write("var src_v6_nodes = %s;\n" % json.dumps(n))
    f.write("var src_v6_edges = %s;\n" % json.dumps(e))
