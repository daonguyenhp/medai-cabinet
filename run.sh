#!/bin/zsh
# Wrapper script to fix libexpat compatibility issue with Python 3.12 on macOS
# Usage: ./run.sh <script.py> [args...]
#        ./run.sh infrastructure/aws_setup.py
#        ./run.sh backend/main.py

export DYLD_LIBRARY_PATH="/usr/local/opt/expat/lib:$DYLD_LIBRARY_PATH"

VENV_PYTHON="/Users/t1tuankhoi/MedAI/medai-cabinet/backend/venv/bin/python3.12"

if [ -z "$1" ]; then
  echo "Usage: ./run.sh <script.py> [args...]"
  exit 1
fi

exec "$VENV_PYTHON" "$@"
