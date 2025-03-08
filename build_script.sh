rm -rf ./dist
python -m build .
yes | sudo pip uninstall --break-system-packages military-symbol
pip install --break-system-packages ./dist/military_symbol-1.2.2.tar.gz
