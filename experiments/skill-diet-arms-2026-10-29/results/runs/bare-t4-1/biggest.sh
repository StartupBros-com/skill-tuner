#!/usr/bin/env bash
# Print the three largest files under ./data with sizes in bytes, largest first.
find ./data -type f -printf '%s\t%p\n' | sort -t$'\t' -k1,1nr | head -n 3 | awk -F'\t' '{print $2 ": " $1}'
