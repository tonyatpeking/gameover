#!/usr/bin/env bash
cd "$(dirname "$0")"


# activate venv
source .venv/bin/activate

# run the python script
python src/gameover.py
