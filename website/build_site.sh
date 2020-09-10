#!/bin/bash
#
# A simple script to build the flat html github IO pages out of our
# in-repo markdown pages as well as the notebook examples.

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
$pythonCmd -m pip install pyyaml
$pythonCmd -m pip install \
    $("$MLOS_ROOT/scripts/parse-pip-requirements-from-environment-yaml.py" "$MLOS_ROOT/source/Mlos.Notebooks/environment.yml")
# FIXME: nbconvert 6.0.1 had an error.
$pythonCmd -m pip install jupyter nbconvert==5.6.1

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

# Make some top level files available in the site.
cp ../LICENSE.txt content/
# Make all *.md files from the repo available in the content tree using the same layout.
(cd $MLOS_ROOT; \
    find \
        *.md \
        build/ \
        documentation/ \
        scripts/ \
        source/ \
        test/ \
        -name '*.md' \
) | while read md_path; do
    md_dir=$(dirname "$md_path")
    md_file=$(basename "$md_path")
    mkdir -p "content/$md_dir"
    if [ "$md_file" == 'README.md' ]; then
        # Except for README files - they should be created like directory indexes.
        # NOTE: Each directory that includes an .md should have one of these.
        cp "$MLOS_ROOT/$md_dir/README.md" "content/$md_dir/_index.md"
    else
        cp "$MLOS_ROOT/$md_path" "content/$md_dir/"
    fi
done

# Make all of the top-level documentation available in the site content.
cp -r "$MLOS_ROOT/documentation/images" content/documentation/

# replace markdown links
# this allows the original files to link on github directly
# while also rendering properly in hugo (which requires no .md in the links)
for content_filepath in $(find content/ -type f -name '*.md'); do
    # Skip some file that are handled manually and are revision controlled.
    if [ "$content_filepath" == 'content/menu/index.md' ]; then
        continue
    fi

    base_filepath=$(echo "$content_filepath" | sed 's|^content/||')
    parent_path=$(dirname "$base_filepath")

    # 1. replace a special fake anchor with a link to the main github repo site
    # (this allows browsing back to the main published source from the website)
    # 2. convert relative paths to be relative to the website root instead
    # 3. strip the .md file ending to replace it with a trailing slash
    # (to be consistent with the hugo md -> html conversion)

    # Also keep a backup for comparison/debugging purposes.

    sed -i.bak -r \
        -e "s|\]\(([./]*[^:#)]+)#mlos-github-tree-view\)|](https://github.com/microsoft/MLOS/tree/main/${parent_path}/\1)|g" \
        -e "s|\]\(([./]*[^:)]+)\)|](/MLOS/${parent_path}/\1)|g" \
        -e "s|\]\(([./]*[^:#)]+)\.md(#[^)]+)?\)|](\1/\2)|g" \
        "$content_filepath"
done

# Get a theme for hugo
if [ ! -d "themes/book" ]; then
    git clone --depth 1 --branch v8 https://github.com/alex-shpak/hugo-book.git themes/book/
fi

if ! [ -x /usr/bin/hugo ]; then
    set -x
    sudo apt-get update >/dev/null
    sudo apt-get -y install hugo
    set +x
fi
