#!/bin/sh

cp -r ../documentation content/
# downgrade html output because hugo doesn't like raw html
jupyter nbconvert ../source/Mlos.Notebooks/*.ipynb --to markdown --output-dir content/notebooks --template nbconvert_template.md.j2 --config jupyter_nbconvert_config.py

# nbconvert and hugo disagree about paths
# this should probably be done via the template
sed -i 's/BayesianOptimization_files/\.\.\/BayesianOptimization_files/g' content/notebooks/BayesianOptimization.md
sed -i 's/SmartCacheOptimization_files/\.\.\/SmartCacheOptimization_files/g' content/notebooks/SmartCacheOptimization.md

# place links to github in notebook files
for f in content/notebooks/*.md; do
    base=$(basename "$f" '.md') # removes .md from file name
    sed -i "s/FILENAME/$base/g" "$f"
done
sed -i 's/FILENAME\.ipynb/BayesianOptimization\.ipynb/g' content/notebooks/*.md

cp ../*.md content/
cp ../LICENSE content/
cp ../README.md content/_index.md
mv content/documentation/README.md content/documentation/_index.md

# replace markdown links
# this allows the original files to link on github directly
# while also rendering properly in hugo (which requires no .md in the links)
sed -i 's/\.md/\//g' content/*.md
sed -i 's/\.md/\//g' content/documentation/*.md


if [ ! -d "themes/book" ]; then
    git clone --depth 1 --branch v8 https://github.com/alex-shpak/hugo-book.git themes/book/
fi
