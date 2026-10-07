#!/usr/bin/env bash
# Spustí dashboard lokálně. Prohlížeč neumí fetch() z file:// — proto server.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8765}"
echo "Dashboard: http://localhost:$PORT"
cd "$ROOT/dashboard" && exec python3 -m http.server "$PORT" --bind 127.0.0.1
