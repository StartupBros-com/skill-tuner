#!/usr/bin/env bash
find ./data -type f -printf '%s %p\n' | sort -rn | head -n 3
