#!/bin/sh

cp -r ../documentation content/
jupyter nbconvert ../source/Mlos.Notebooks/*.ipynb --to markdown --output-dir content/notebooks

cp ../*.md content/
cp ../LICENSE content/
mv content/README.md content/_index.md

if [ ! -d "themes/book" ]; then
    git clone --depth 1 https://github.com/alex-shpak/hugo-book.git themes/book/
fi