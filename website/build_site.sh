#!/bin/bash
#
# A simple script to build the github IO pages out of

# be strict
set -eu

# be verbose
#set -x

# ensure we're in the right folder
scriptdir=$(readlink -f "$(dirname "$0")")
MLOS_ROOT=$(readlink -f "$scriptdir/..")
cd "$MLOS_ROOT/website"

. "$MLOS_ROOT/scripts/util.sh"
pythonCmd=$(getPythonCmd)

# Make sure we have all the requirements for generating notebooks.
$pythonCmd -m pip install -e "$MLOS_ROOT/source/Mlos.Python/"
$pythonCmd -m pip install \
    $("$MLOS_ROOT/scripts/parse-pip-requirements-from-environment-yaml.py" "$MLOS_ROOT/source/Mlos.Notebooks/environment.yml")
$pythonCmd -m pip install jupyter nbconvert

# Make all of the top-level documentation available in the site content.
mkdir -p content
cp -r "$MLOS_ROOT/documentation" content/

# execute and render the notebooks to html
# downgrade html output because hugo doesn't like raw html
mkdir -p content/notebooks
notebooks='BayesianOptimization SmartCacheOptimization'
for nb in $notebooks; do
    nb_path="$MLOS_ROOT/source/Mlos.Notebooks/$nb.ipynb"
    echo "Executing and rendering $nb_path"
    $pythonCmd -m jupyter nbconvert "$nb_path" \
        --to markdown --output-dir content/notebooks/ \
        --template nbconvert_template.md.j2 --config jupyter_nbconvert_config.py
# TODO: Execute the notebooks during website build.
# Currently the SmartCacheOptimization throws an error.
# NOTE: These are also somewhat expensive to execute on every single CI.
#        --execute \
#        --ExecutePreprocessor.kernel_name=python3 \
#        --ExecutePreprocessor.timeout=600 \
done

# place links to github in notebook files
# (builds off the nbconvert template)
for f in content/notebooks/*.md; do
    base=$(basename "$f" '.md') # removes .md from file name
    sed -i "s/FILENAME/$base/g" "$f"
done
sed -i 's/FILENAME\.ipynb/BayesianOptimization\.ipynb/g' content/notebooks/*.md

# Make top level md files available in the site.
cp ../LICENSE.txt content/
cp ../*.md content/
# But make a few of them the directory level index.
mv content/README.md content/_index.md
mv content/documentation/README.md content/documentation/_index.md

# replace markdown links
# this allows the original files to link on github directly
# while also rendering properly in hugo (which requires no .md in the links)
# TODO: FIXME:
for content_filepath in $(find content/ -type f -name '*.md'); do
    # Skip some file that are handled manually and are revision controlled.
    if [ "$content_filepath" == 'content/menu/index.md' ]; then
        continue
    fi

    base_filepath=$(echo "$content_filepath" | sed 's|^content/||')
    parent_path=$(dirname "$base_filepath")
    sed -i.bak -r \
        -e "s|\]\(([./]*[^:#)]+)#mlos-github-tree-view\)|](https://github.com/microsoft/MLOS/tree/main/${parent_path}/\1)|g" \
        -e "s|\]\(([./]*[^:)]+)\)|](/MLOS/${parent_path}/\1)|g" \
        -e "s|\]\(([./]*[^:#)]+)\.md(#[^)]+)?\)|](\1/\2)|g" \
        "$content_filepath"
done
# FIXME:
#sed -i 's/\.md/\//g' content/*.md
#sed -i 's/\.md/\//g' content/documentation/*.md

# Get a theme for hugo
if [ ! -d "themes/book" ]; then
    git clone --depth 1 --branch v8 https://github.com/alex-shpak/hugo-book.git themes/book/
fi
