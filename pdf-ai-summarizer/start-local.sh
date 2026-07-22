#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "PDF AI Summarizer"
echo "Project root: ${PROJECT_ROOT}"
echo
echo "Backend and frontend startup will be enabled after the health-check and frontend steps are implemented."
