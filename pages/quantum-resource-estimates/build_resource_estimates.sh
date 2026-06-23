#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 scripts/render_resource_estimates.py --base .
