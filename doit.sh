#!/usr/bin/env sh
set -eu
python -m unittest discover -s tests -v
python -m compileall -q walkforwardlab tests
./run.sh >/dev/null
echo "WalkForwardLab verification complete"
