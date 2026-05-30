#!/usr/bin/env bash
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

"$PYTHON_BIN" -m pygbag --ume_block 0 --template static/sudoku.tmpl .
