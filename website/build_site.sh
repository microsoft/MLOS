#!/bin/sh

cp -r ../documenation content/
jupyter nbconvert ../source/Mlos.Notebooks --to markdown --output-dir content/notebooks
