rm -rf ./dist
python -m build .
yes | sudo pip uninstall military-symbol
pip install ./dist/military_symbol-1.0.7.post1.tar.gz