import csv
from collections import defaultdict
from ripe.atlas.cousteau import (Traceroute, AtlasSource, AtlasCreateRequest)
from datetime import datetime
import random
import os
import json

with open('dual-stacked-probes.csv') as f:
    csv_r = csv.reader(f)

    probes_per_as = defaultdict(list)
    for row in csv_r:
        probes_per_as[row[2]].append(row[0])

# print(probes_per_as)
probe_sample = random.sample(probes_per_as.items(), 10)

# Get a list of dual-stacked sites from somewhere
sites = ['www.comcast.net', 'www.facebook.com',
         'www.google.com', 'www.apnic.net']
# sites = ['www.comcast.net']

with open(os.path.join(os.environ['HOME'], '.auth/ripe-atlas')) as f:
    ATLAS_API_KEY = f.readline().rstrip("\n")

# Execute some measurements
# print(probe_sample)
msm_list = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for (asn, probe_list) in probe_sample:
    print(probe_list)
    source = AtlasSource(type='probes', value=",".join(probe_list),
                         requested=len(probe_list))
    for family in [4, 6]:
        for dest in sites:
            description = "RIPE72: Dual stack trace from %s to %s" % (asn, dest)
            traceroute = Traceroute(af=family, target=dest,
                                    description=description,
                                    protocol='ICMP')
            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=ATLAS_API_KEY,
                is_oneoff=True,
                sources=[source],
                measurements=[traceroute]
            )

            (is_success, response) = atlas_request.create()
            if is_success:
                msm_list[asn][dest][family] = [m for m in response[
                    'measurements']]

with open('dual-stack-msm.json', 'wb') as f:
    json.dump(msm_list, f)
