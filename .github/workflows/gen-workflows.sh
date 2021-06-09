#!/bin/bash

set -eux

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

# Prepare the common rules for each version using the template.
for UbuntuVersion in {16,18,20}.04; do
    if [ "$UbuntuVersion" == '20.04' ]; then
        DockerPublishJobNeeds='[prep-vars, docker-image-fresh-build, docker-image-cached-build, linux-build-test, linux-python-checks, build-publish-website]'
    else
        DockerPublishJobNeeds='[prep-vars, docker-image-fresh-build, docker-image-cached-build, linux-build-test]'
    fi

    cp ./ubuntu.yml.tmpl ./ubuntu-$UbuntuVersion.yml
    sed -i \
        -e "s/%UBUNTU_VERSION%/$UbuntuVersion/g" \
        -e "s/%DockerPublishJobNeeds%/$DockerPublishJobNeeds/g" \
        ./ubuntu-$UbuntuVersion.yml
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
