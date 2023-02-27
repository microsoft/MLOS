#!/bin/sh

# Prep some files for the devcontainer build in a way that's cross platform.
# We do this by running this script from a container that has the tools we need
# and generates files with the right encodings so that it's more cacheable
# across platforms.

set -eu

set -x

scriptdir=$(dirname "$(readlink -f "$0")")
# Start in the root of the repository.
cd "$scriptdir/../../../"

# Make sure the .env file exists for the devcontainer to load.
if [ ! -f .env ]; then
    echo "Creating empty .env file for devcontainer."
    touch .env
fi

# Create (partial) conda environment file for the container to build from.
# Note: this should make it more cacheable as well.
# See Also: updateContentCommand in .devcontainer/devcontainer.json
echo "Creating base mlos_core_deps.yml environment file for devcontainer context."
if [ -d .devcontainer/tmp ]; then
    rm -rf .devcontainer/tmp
fi
mkdir -p .devcontainer/tmp/
cat ./conda-envs/mlos_core.yml \
    | sed 's|#.*||' \
    | egrep -v -e '--editable' -e '^\s*$' \
    | tee .devcontainer/tmp/mlos_core_deps.yml
md5sum .devcontainer/tmp/mlos_core_deps.yml

cp -v doc/requirements.txt .devcontainer/tmp/doc.requirements.txt

# Try to grab the requirements.txt files for the python packages.
tmpdir=$(mktemp -d)
get_python_deps() {
    local pkg="$1"
    touch ".devcontainer/tmp/$pkg.requirements.txt"
    python3 "$pkg"/setup.py egg_info --egg-base "$tmpdir/"
    cat "$tmpdir/$pkg.egg-info/requires.txt" \
        | grep -v -e '^\[' -e '^\s*$' \
        | grep -v '^mlos-core' \
        | sort -u \
        > ".devcontainer/tmp/$pkg.requirements.txt"
}
for pkg in mlos_core mlos_bench; do
    get_python_deps "$pkg" || true
done
rm -rf "$tmpdir"
cat .devcontainer/tmp/*.requirements.txt | sort -u > .devcontainer/tmp/combined.requirements.txt
