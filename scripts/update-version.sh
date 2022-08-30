#!/bin/bash

set -eu

NEWVERS=${NEWVERS:-0.0.4}

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir/.."

sed -i -r -e "s/-[0-9]+\.[0-9]+\.[0-9]+([~]?[a-z0-9]+)?-py/-$NEWVERS-py/" \
    README.md \
    doc/source/installation.rst

quotechars='"'
quotechars+="'"

sed -i -r 's/((_VERSION|release)\s*=\s*['$quotechars'])[0-9]+\.[0-9]+\.[0-9]+([~]?[a-z0-9]+)?(['$quotechars'])/\1'${NEWVERS}'\4/' \
    mlos_{core,bench}/setup.py \
    doc/source/conf.py
