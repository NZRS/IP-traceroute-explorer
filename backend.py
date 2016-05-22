import bottle
import json
from ripe.atlas.sagan import TracerouteResult
import networkx as nx
import requests
from collections import defaultdict
import math

stat_ripe = "https://stat.ripe.net/data/routing-status/data.json"

with open('metadata.json') as f:
    exp_config = json.load(f)
# exp_config = {
#     '0':{
#         'ipv4': '3806401',
#         'ipv6': '3806402',
#         'label': 'Denmark to Comcast'
#     },
#     '1':{
#         'ipv4': '3814200',
#         'ipv6': '3814201',
#         'label': 'Somewhere to Google'
#     }
# }

addr2as = {}
with open('as_map.json') as f:
    addr2as = json.load(f)


def get_addr_as(a):
    return addr2as.get(a, None)


def transform_graph(g, origin_asn, dest_asn):
    nl = []
    n_idx = {}
    idx = 0
    for n in g.nodes_iter():
        # idx = g.node[n]['index']
        if n == origin_asn:
            nl.append({'label': n, 'id': idx, 'value': g.node[n]['hops'],
                       'x': 10, 'y': 140, 'color': 'green'})
        elif n == dest_asn:
            nl.append({'label': n, 'id': idx, 'value': g.node[n]['hops'],
                       'x': 600, 'y': 140, 'color': 'yellow'})
        else:
            nl.append({'label': n, 'id': idx, 'value': g.node[n]['hops']})
        n_idx[n] = idx
        idx += 1

    el = [{'to': n_idx[t],
           'from': n_idx[s],
           'value': round(math.sqrt(d['rtt']), 3),
           'label': d['rtt']} for s, t, d in g.edges_iter(data=True)]

    return nl, el


bottle.app().catchall = False
bottle.debug(True)


@bottle.hook('after_request')
def enable_cors():
    bottle.response.headers['Access-Control-Allow-Origin'] = '*'


@bottle.route('/path/<family>')
def index(family):
    exp_id = bottle.request.query.id
    msm_file = exp_config[exp_id][family][0]

    # Read the data
    G = nx.DiGraph()
    hop_cnt = defaultdict(int)
    hop_idx = defaultdict(int)
    origin_asn = None
    with open("%s.json" % msm_file) as f:
        res_blob = json.load(f)

        seq = []
        for res_set in res_blob:
            sagan_res = TracerouteResult(res_set)

            asn = get_addr_as(sagan_res.origin)
            prev_asn = asn
            origin_asn = asn
            hop_cnt[asn] += 1
            for hop in sagan_res.hops:
                hop_addr = set()
                for packet in hop.packets:
                    if packet.origin is None:
                        continue

                    hop_addr.add(packet.origin)

                for a in hop_addr:
                    asn = get_addr_as(a)
                    if asn is not None:
                        hop_cnt[asn] += 1
                        hop_idx[asn] = hop.index
                        addr2as[a] = asn
                    else:
                        hop_cnt[prev_asn] += 1
                        hop_idx[prev_asn] = hop.index
                        addr2as[a] = prev_asn
                    if asn is not None and prev_asn != asn:
                        G.add_edge(prev_asn, asn, rtt=hop.median_rtt)
                        prev_asn = asn

    for n in G.nodes_iter():
        G.node[n]['hops'] = hop_cnt[n]
        G.node[n]['index'] = hop_idx[n]

    n, e = transform_graph(G, origin_asn, asn)

    # Return an object
    return {'nodes': n, 'edges': e}


@bottle.route('/experiment')
def list_experiment():
    return {'items': [dict((('id', k), ('label', v['label']))) for k,
                                                                   v in exp_config.iteritems()]}


bottle.run(host='localhost', port=8080)

