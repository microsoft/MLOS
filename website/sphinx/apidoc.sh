#!/bin/sh

# ensure we're in the right folder
scriptdir=$(readlink -f "$(dirname "$0")")
echo $scriptdir
echo `pwd`
cd "$scriptdir/.."
cd website/sphinx

echo "Generating Python API rst files"

sphinx-apidoc -o api -t _templates ../../source/Mlos.Python/mlos ../../source/Mlos.Python/mlos/unit_tests/* -d 1 -f -e
