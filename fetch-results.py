import json
from ripe.atlas.cousteau import AtlasResultsRequest
from datetime import datetime
from collections import defaultdict

with open('dual-stack-msm.json') as f:
    msm = json.load(f)

idx = 0
metadata = {}
for src, v1 in msm.iteritems():
    for dst, v2 in v1.iteritems():
        entry = defaultdict(list)
        for af, msm_list in v2.iteritems():
            for msm_id in msm_list:
                args = {
                    'msm_id': msm_id
                }

                is_success, results = AtlasResultsRequest(**args).create()
                print("From AS%s to %s" % (src, dst))
                if is_success:
                    with open('%s.json' % msm_id, 'wb') as f:
                        json.dump(results, f)

                entry[af] = results

        metadata[idx] = {'ipv4': entry['4'],
                         'ipv6': entry['6'],
                         'label': "From AS%s to %s" % (src, dst)}

        idx += 1

with open('metadata.json', 'wb') as f:
    json.dump(metadata, f)
