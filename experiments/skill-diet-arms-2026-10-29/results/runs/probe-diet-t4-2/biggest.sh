#!/usr/bin/env bash
# Print the three largest files under ./data as "<bytes> <path>", largest first.
find ./data -type f -printf '%s %p\n' | sort -rn | head -n 3
