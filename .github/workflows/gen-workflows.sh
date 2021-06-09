#!/bin/bash

set -eux

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

# Prepare the common rules for each version using the template.
for UbuntuVersion in {16,18,20}.04; do
    cat ./ubuntu.yml.tmpl | sed "s/%UBUNTU_VERSION%/$UbuntuVersion/g" > ./ubuntu-$UbuntuVersion.yml
done
# Append the extra rules to that file.
grep -q '^[ ]*#%EXTRA_RULES%#$' ./ubuntu-20.04.yml
sed -i -e '/^[ ]*#%EXTRA_RULES%#$/{
    s/^[ ]*#%EXTRA_RULES%#$//
    r ./ubuntu-20.04.yml.extra
}' ubuntu-20.04.yml
if grep -q '^[ ]*#%EXTRA_RULES%#$' ./ubuntu-20.04.yml; then
    echo 'ERROR: Failed to replace EXTRA_RULES.' >&2
    exit 1
fi

echo "OK"
