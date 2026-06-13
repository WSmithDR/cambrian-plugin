#!/usr/bin/env bash
# Smoke test de cambrian-plugin: el CLI responde y el corpus hace round-trip.
# Escribe en un data dir temporal; nunca toca el real. Exit 0 = ok.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export CAMBRIAN_DATA_DIR="$TMP"

CLI="python3 $ROOT/bin/cambrian"

echo "1. add idea"
ID="$($CLI corpus add --topic "_smoke_" --lens minimalista --text "idea de smoke")"
[ -n "$ID" ] || { echo "FAIL: add no devolvió id"; exit 1; }

echo "2. list contiene la idea"
$CLI corpus list --topic "_smoke_" | grep -q "idea de smoke" || { echo "FAIL: list"; exit 1; }

echo "3. mark aceptada"
$CLI corpus mark --topic "_smoke_" --id "$ID" --status aceptada >/dev/null
$CLI corpus list --topic "_smoke_" | grep -q '"status": "aceptada"' || { echo "FAIL: mark"; exit 1; }

echo "4. seen devuelve la idea"
$CLI corpus seen --topic "_smoke_" | grep -q "idea de smoke" || { echo "FAIL: seen"; exit 1; }

echo "OK: smoke test passed"
