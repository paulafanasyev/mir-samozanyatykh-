#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q app tests tools
python tools/security_regression_check.py
python tools/api_contract_audit.py
ruff check app tests tools
