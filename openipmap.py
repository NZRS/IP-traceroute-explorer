import csv
import json
from ripe.atlas.sagan import TracerouteResult

import logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

def read_openipmap_dump(filename):
    ret = {}
    csvfile = open(filename, 'rb')
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in csvreader:
        ip = row[0]
        geostr = row[3]
        if geostr == 'None':
            continue
        ret[ip] = {
            'ip': ip,
            'lat': row[1],
            'lon': row[2],
            'geostr': geostr,
            'hostname': row[4],
            'changed': row[5],
            'confidence': row[6],
        }
    return ret

def read_probes(probefile):
    ret = {}
    fd = open(probefile, 'rb')
    probe_list = json.load(fd)
    for probe in probe_list:
        ret[probe['address_v4']] = probe
        ret[probe['address_v6']] = probe
        ret[probe['id']] = probe
    return ret

ipmapdata = read_openipmap_dump('openipmap.csv')
probes = read_probes('data/probes.json')
#print('loaded openipmap')

results_file = 'combined/sample.json'
results_file = 'combined/results.json'

res_fd = open(results_file, 'rb')
res_blob = json.load(res_fd)
#print('loaded results')

traces = {}

i = 0
for res in res_blob:
    sagan_res = TracerouteResult(res)

    src = sagan_res.origin
    dst = sagan_res.destination_address
    af = sagan_res.af

    geocodedips = {}

    packet_cnt = 0
    geocoded = 0
    for hop in reversed(sagan_res.hops):
        for packet in hop.packets:
            packet_cnt += 1
            if ipmapdata.has_key(packet.origin):
                geocoded += 1
                geoip = ipmapdata[packet.origin]
                geocodedips[packet.origin] = geoip

    georatio = geocoded/float(packet_cnt)
    t = (georatio, src, dst, packet_cnt, geocoded)

    src_probe = probes[sagan_res.probe_id]
    #src_probe = probes[src] - some src ip addresses are slightly wrong in the probes file
    dst_probe = probes[dst]

    pair = {}
    trace_key = '%s_%s' % (src_probe['id'], dst_probe['id'])
    try:
        pair = traces[trace_key]
    except KeyError:
        pair = {}
        traces[trace_key] = pair
    pair[af] = {
        't': t,
        'trace': res,
        'geoips': geocodedips,
        'src': src_probe,
        'dst': dst_probe,
    }

out_traces = []

for tid in traces:
    trace = traces[tid]
    if trace.has_key(4) and trace.has_key(6):
        ratio = (trace[4]['t'][0] + trace[6]['t'][0]) / 2
        t = (ratio,) + trace[4]['t'] + trace[6]['t']
        if ratio >= 0.5:
            print('%.2f,\t,%.2f,%s,%s,%d,%d,\t,%.2f,%s,%s,%d,%d' % t)
            out_traces.append(trace)


out = open('geocodedtraces.json', 'wb')
json.dump(out_traces, out)
