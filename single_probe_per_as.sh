#!/bin/sh
cat dual-stacked-probes.csv | grep : | grep -v asn_v4 | awk 'BEGIN { FS="," }; { printf "%08d,%06d,%d,%s,%s\n", $3, $1, $2, $4, $5 }' | sort -t, -k1,2r | uniq -w8 > single_probe_per_as.csv
