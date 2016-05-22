import json
from ripe.atlas.sagan import TracerouteResult
import requests
import sys
from multiprocessing import Pool
import codecs


stat_ripe = "https://stat.ripe.net/data/routing-status/data.json"
addr2as = {}


def get_addr_as(a):
    if a in addr2as:
        return addr2as[a]

    print("** Mapping %s" % a)
    r = requests.get(stat_ripe, params={'resource': a})
    response = r.json()

    origin = set()
    try:
        origin = set([o['origin'] for o in response['data']['origins']])
    except KeyError:
        return (a, None)

    if len(origin) > 0:
        return (a, list(origin)[0])

    return (a, None)


addr_list = set()
for msm_f in sys.argv[1:]:
    print("Parsing %s" % msm_f)
    with open(msm_f) as f:
        res_blob = json.load(f)

        seq = []
        for res_set in res_blob:
            sagan_res = TracerouteResult(res_set)

            addr_list.add(sagan_res.origin)
            for hop in sagan_res.hops:
                hop_addr = set()
                for packet in hop.packets:
                    if packet.origin is None:
                        continue

                    addr_list.add(packet.origin)

pool = Pool(processes=6)
results = pool.map(get_addr_as, addr_list)
for r in results:
    if r[1] is not None:
        addr2as[r[0]] = r[1]

print(addr2as)

with codecs.open('as_map.json', 'wb', encoding='UTF-8') as f:
    json.dump(addr2as, f)

