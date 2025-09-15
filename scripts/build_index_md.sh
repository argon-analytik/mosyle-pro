#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

awk -F'\t' 'BEGIN{print "# Mosyle Index\n"} {printf "* **%s** — %s  \n", $1,$2}' index.tsv > index.md
