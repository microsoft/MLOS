#!/bin/sh

cp -r ../documentation content/
jupyter nbconvert ../source/Mlos.Notebooks/*.ipynb --to markdown --output-dir content/notebooks

cp ../README.md content/_index.md

git clone --depth 1 https://github.com/alex-shpak/hugo-book.git themes/book/