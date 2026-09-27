#!/usr/bin/env bash
# Prepare material uassets and a cookable map using an installed UE 5.4 editor.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -z "${UE_ROOT:-}" ]]; then echo 'Set UE_ROOT to a UE5.4 root' >&2; exit 2; fi
EDITOR="$UE_ROOT/Engine/Binaries/Linux/UnrealEditor"
if [[ ! -x "$EDITOR" ]]; then echo "Missing UnrealEditor: $EDITOR" >&2; exit 2; fi
"$EDITOR" "$ROOT/AfterSignal.uproject" -unattended -nop4 -nosplash -NullRHI -ExecutePythonScript="$ROOT/scripts/import_materials.py"
"$EDITOR" "$ROOT/AfterSignal.uproject" -unattended -nop4 -nosplash -NullRHI -ExecutePythonScript="$ROOT/scripts/create_level.py"
if [[ ! -f "$ROOT/Content/Maps/RelayRoad.umap" ]]; then
    echo 'Editor did not create Content/Maps/RelayRoad.umap' >&2; exit 1
fi
for name in ForestGround RoadAsphalt Concrete; do
    if [[ ! -f "$ROOT/Content/Materials/M_${name}.uasset" ]]; then
        echo "Editor did not create material M_${name}" >&2; exit 1
    fi
done
printf 'Prepared UE project map and material assets.\n'
