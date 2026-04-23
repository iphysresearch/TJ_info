#!/bin/bash
# Manual deployment script for GitHub Pages

set -e

echo "Building Hugo site..."
rm -rf public
hugo --minify

echo "Deploying to gh-pages branch..."
cd public
git init
git checkout -b gh-pages
git add -A
git commit -m "Deploy $(date '+%Y-%m-%d %H:%M:%S')"
git remote add origin https://github.com/iphysresearch/TJ_info.git
git push -f origin gh-pages

echo "Done! Site will be live at https://iphysresearch.github.io/TJ_info/"
