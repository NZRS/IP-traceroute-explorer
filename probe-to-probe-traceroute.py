import json
import argparse
import urllib2
import random
import time
import sys
import os
import os.path
from collections import defaultdict
import math


def load_existing(source_dir, filename):
    e = []
    file_loc = "{}/{}".format(source_dir, filename)
    if os.path.isfile(file_loc):
        with open(file_loc, 'rb') as s_file:
            e = json.load(s_file)
    return e


def read_auth(filename):
    with open(filename, 'rb') as auth_file:
        key = auth_file.readline()[:-1]

    return key

def probe_ids(probe_set, myid):
    return [str(id) for id in probe_set-{myid}]

def chunks(l, n):
    n = max(1, n)
    chunk_size = int(math.ceil(len(l)/float(n)))
    return [l[i:i + chunk_size] for i in range(0, n*chunk_size, chunk_size)]

def schedule_measurement(af, dest, probes):
    parts = chunks(probes, 3)
    for part in parts:
        schedule_measurement_part(af, dest, part)

msm_list = []
failed_msm = []

def schedule_measurement_part(af, dest, probes):
        global msm_list, failed_msm
        status = do_schedule_measurement(af, dest, probes)
        msm_list = msm_list + status['list']
        failed_msm = failed_msm + status['failed']

def do_schedule_measurement(af, dest, probes):
    msm_status = defaultdict(list)

    data = {"definitions": [
        {
            "target": dest,
            "description": "Traceroute to {}".format(dest),
            "type": "traceroute",
            "protocol": "ICMP",
            "paris": 16,
            "af": af,
            "is_oneoff": True,
            "can_visualize": False,
            "is_public": False
        }],
        "probes": [{"requested": len(probes), "type": "probes", "value": ",".join(probes)}]
        }

    try:
        req_data = json.dumps(data)
        request = urllib2.Request(base_url)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        conn = urllib2.urlopen(request, req_data)
        results = json.load(conn)
        print results
        print req_data
        for m in results['measurements']:
            msm_status['list'].append(m)
        conn.close()
        # This sleep is important to give time to the scheduled measurements to complete before trying more.
        time.sleep(3)
    except urllib2.HTTPError as e:
        msm_status['failed'].append(dest)
        print "Fatal Error: {}".format(e.read())
        print req_data

    return msm_status

parser = argparse.ArgumentParser("Creates probe to probe traceroutes")
parser.add_argument('--datadir', required=True, help="directory to save output")
args = parser.parse_args()

if not os.path.exists(args.datadir):
    os.makedirs(args.datadir)

authkey = read_auth("create-key.txt")
if authkey is None:
    print "Auth file not found, aborting"
    sys.exit(1)

with open('data/probes.json', 'rb') as probe_file:
    probe_list = json.load(probe_file)

base_url = "https://atlas.ripe.net/api/v1/measurement/?key={}".format(authkey)

probe_id_set = set([probe['id'] for probe in probe_list])

i = 0
for probe in probe_list:
    i += 1
    if i <= 14:
        continue
    if i > 100:
        break
    probeless_set = probe_ids(probe_id_set, probe['id'])
    schedule_measurement(4, probe['address_v4'], probeless_set)
    schedule_measurement(6, probe['address_v6'], probeless_set)

existing_msm = load_existing(args.datadir, 'measurements.json')
with open('{}/measurements.json'.format(args.datadir), 'wb') as msm_file:
    json.dump(msm_list + existing_msm, msm_file)

existing_failures = load_existing(args.datadir, 'failed-probes.json')
with open('{}/failed-probes.json'.format(args.datadir), 'wb') as failed_file:
    json.dump(failed_msm + existing_failures, failed_file)
