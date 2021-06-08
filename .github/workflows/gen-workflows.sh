#!/bin/bash

set -eu

for UbuntuVersion in {16,18,20}.04; do
    cat ./ubuntu.yml.tmpl | sed "s/%UBUNTU_VERSION%/$UbuntuVersion/g" > ./ubuntu-$UbuntuVersion.yml
done
