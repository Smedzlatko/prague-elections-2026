#!/usr/bin/env bash
# Stáhne otevřená data ČSÚ pro komunální volby 2026 a 2022 do .cache/
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="$ROOT/.cache"
mkdir -p "$CACHE"

get() { # url, outfile
  if [ -f "$CACHE/$2" ]; then echo "  = $2 (z cache)"; else
    echo "  ↓ $2"; curl -sSL --max-time 300 -o "$CACHE/$2" "$1"
  fi
}

echo "== Komunální volby 2026 =="
get "https://volby.gov.cz/opendata/kv2026/KV2026reg20260923_csv.zip"   kv2026_reg.zip
get "https://volby.gov.cz/opendata/kv2026/KV2026ciselniky20260923_csv.zip" kv2026_cis.zip

echo "== Komunální volby 2022 (historie, mandáty) =="
get "https://volby.gov.cz/opendata/kv2022/KV2022reg20260328_csv.zip"   kv2022_reg.zip
get "https://volby.gov.cz/opendata/kv2022/KV2022ciselniky20260328_csv.zip" kv2022_cis.zip

echo "== Rozbalení =="
for z in kv2026_reg kv2026_cis kv2022_reg kv2022_cis; do
  rm -rf "$CACHE/$z"; mkdir -p "$CACHE/$z"
  unzip -o -q "$CACHE/$z.zip" -d "$CACHE/$z"
done
echo "Hotovo. Data v $CACHE"
