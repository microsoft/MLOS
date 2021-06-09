#!/bin/bash
# gen-workflows.sh
# 2021-06-08
# bpkroth
#
# A simple script to template out separate github action workflow configs for
# each version of ubuntu we support so that they can be retried independently.

set -eux

scriptdir=$(dirname "$(readlink -f "$0")")
cd "$scriptdir"

# Prepare the common rules for each version using the template.
for UbuntuVersion in {16,18,20}.04; do
    # Only one of the Ubuntu versions runs some of the extra checks (see below).
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
# Insert the extra rules to just one of the Ubuntu version workflow files.
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
exit 0
