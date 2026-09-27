#!/usr/bin/env bash
# Run only on an Unreal Engine 5.4 host with matching Android SDK/NDK/JDK.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UAT="${UE_ROOT:-}/Engine/Build/BatchFiles/RunUAT.sh"
if [[ -z "${UE_ROOT:-}" || ! -x "$UAT" ]]; then
  echo 'Missing UE_ROOT: point it at an installed UE5 root with Engine/Build/BatchFiles/RunUAT.sh' >&2
  exit 2
fi
if [[ ! -f "$ROOT/AfterSignal.uproject" ]]; then echo 'Project not found' >&2; exit 2; fi
if [[ -z "${ANDROID_HOME:-}" || ! -d "$ANDROID_HOME" ]]; then
  echo 'Missing ANDROID_HOME (matching UE Android SDK/NDK required)' >&2; exit 2
fi
if [[ -z "${JAVA_HOME:-}" || ! -d "$JAVA_HOME" ]]; then
  echo 'Missing JAVA_HOME (matching UE JDK required)' >&2; exit 2
fi
if [[ ! -f "$ROOT/Content/Maps/RelayRoad.umap" ]]; then
  echo 'Missing cooked map source: run scripts/prepare-ue-project.sh in UE5 first' >&2; exit 2
fi
mkdir -p "$ROOT/BuildOutput"
"$UAT" BuildCookRun -project="$ROOT/AfterSignal.uproject" -noP4 -platform=Android -targetplatform=Android -clientconfig=Development -build -cook -stage -pak -archive -archivedirectory="$ROOT/BuildOutput" -utf8output
APK="$(find "$ROOT/BuildOutput" -type f -name '*.apk' -print -quit)"
if [[ -z "$APK" || ! -s "$APK" ]]; then echo 'Packaging ended without a nonempty APK' >&2; exit 1; fi
printf 'APK created: %s\n' "$APK"
