#!/usr/bin/env bash
# Print the three largest files under ./data with sizes in bytes, largest first.
find ./data -type f -printf '%s %p\n' | sort -nr | head -n 3
