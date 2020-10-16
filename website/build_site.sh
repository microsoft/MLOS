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
    $($pythonCmd "$MLOS_ROOT/scripts/parse-pip-requirements-from-environment-yaml.py" "$MLOS_ROOT/source/Mlos.Notebooks/environment.yml")
# FIXME: nbconvert 6.0.1 had an error.
$pythonCmd -m pip install jupyter nbconvert==5.6.1

function RenderNotebook()
{
    local nb_path="$1"
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

    # place links to github in notebook files
    # (builds off the nbconvert template)
    nb_basename=$(basename "$nb_path" '.ipynb') # removes .ipynb from file name
    nb_relative_path="$(realpath --relative-to="$MLOS_ROOT" "$(readlink -f "$nb_path")")"
    sed -i "s|THE_PATH_TO_NOTEBOOK_FROM_MLOS_ROOT|$nb_relative_path|g" "content/notebooks/$nb_basename.md"
}

# execute and render the notebooks to html
# downgrade html output because hugo doesn't like raw html
mkdir -p content/notebooks
# Restricted set of notebooks that are rendered for inclusion on the webpage:
mlos_notebooks='BayesianOptimization SmartCacheOptimization SmartCacheCPP'
for nb in $mlos_notebooks; do
    RenderNotebook "$MLOS_ROOT/source/Mlos.Notebooks/$nb.ipynb"
done
# Plus some external project notebooks:
RenderNotebook "$MLOS_ROOT/external/leveldb/LevelDbTuning.ipynb"

# Make notebook images available in the website:
mkdir -p content/notebooks/images/
cp -r $MLOS_ROOT/external/leveldb/images/*.png content/notebooks/images/

# Provide an index file for viewing the set of notebooks that we render at
# http://microsoft.github.io/MLOS/notebooks/
notebooks=$(find content/notebooks/ -name '*.md' -printf '%f\n' | sed 's/\.md$//')
cat > content/notebooks/_index.md <<HERE
# MLOS Sample Notebooks

HERE
for nb in $notebooks; do
    cat >> content/notebooks/_index.md <<HERE
- [${nb}](./${nb}.md)
HERE
done

# Make some top level files available in the site.
cp ../LICENSE.txt content/
# Make all *.md files from the repo available in the content tree using the same layout.
(cd $MLOS_ROOT; \
    find \
        *.md \
        build/ \
        documentation/ \
        external/ \
        scripts/ \
        source/ \
        test/ \
        -name '*.md' -or \
        -name '*.png' -or \
        -name '*.svg' \
) | while read path; do
    dir=$(dirname "$path")
    file=$(basename "$path")
    mkdir -p "content/$dir"
    if [ "$file" == 'README.md' ]; then
        # Except for README files - they should be created like directory indexes.
        # NOTE: Each directory that includes an .md should have one of these.
        cp "$MLOS_ROOT/$dir/README.md" "content/$dir/_index.md"
    else
        cp "$MLOS_ROOT/$path" "content/$dir/"
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
    if [ "$parent_path" == '.' ]; then
        parent_path=''
    elif [ -n "$parent_path" ]; then
        parent_path="${parent_path}/"
    fi

    # 1. replace a special fake anchor with a link to the main github repo site
    # (this allows browsing back to the main published source from the website)
    # 2. convert relative paths to be relative to the website root instead
    # 3. strip the .md file ending to replace it with a trailing slash
    # (to be consistent with the hugo md -> html conversion)
    # 4. Strip any unnecessary '/./' path components we introduce by doing that.

    # Also keep a backup for comparison/debugging purposes.

    sed -i.bak -r \
        -e "s|\]\(([./]*[^:#)]+)#mlos-github-tree-view\)|](https://github.com/microsoft/MLOS/tree/main/${parent_path}\1)|g" \
        -e "s|\]\(([./]*[^:#)]+)(#[^)]*)?\)|](/MLOS/${parent_path}\1\2)|g" \
        -e "s|\]\(([./]*[^:#)]+)\.md(#[^)]*)?\)|](\1/\2)|g" \
        -e "s|\]\(([^)]*)/\./([^)]*)\)|](\1/\2)|g" \
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
