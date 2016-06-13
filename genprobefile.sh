#!/bin/sh
mkdir -p data
cat single_probe_per_as.csv | sed -e 's/,/\t/g' | awk '{ print "{\"id\": " $2 ", \"asn\": "  $1 ", \"address_v4\": \"" $4 "\", \"address_v6\": \"" $5 "\"},"}' | grep -v v4-v6-works  | grep -v probeid | sed -e 's/: 0\+/: /g' > probes.tmp
truncate --size=-2 probes.tmp
(echo '['; cat probes.tmp; echo ']') > data/probes.json
rm -f probes.tmp
