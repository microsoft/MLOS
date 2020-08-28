#!/bin/sh

cp -r ../documentation content/
jupyter nbconvert ../source/Mlos.Notebooks/*.ipynb --to markdown --output-dir content/notebooks

cp ../CODE_OF_CONDUCT.md content/Code_of_conduct.md
cp ../CONTRIBUTING.md content/Contributing.md
cp ../LICENSE content/license
cp ../README.md content/_index.md
mv content/documentation/README.md content/documentation/_index.md
mv content/documentation/05-Test.md content/documentation/03-Test.md
rm content/documentation/03-ExampleUsage.md
rm content/documentation/04-Contributing.md
rm content/documentation/06-Debug.md
rm content/documentation/Glossary.md



if [ ! -d "themes/book" ]; then
    git clone --depth 1 https://github.com/alex-shpak/hugo-book.git themes/book/
fi