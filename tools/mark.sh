#!/usr/bin/env bash
# Setzt eine Zeitmarke für Schalttests (läuft parallel zu tools/capture.sh).
# Nutzt kein MQTT, schreibt nur lokal nach samples/raw/markers.tsv.
#
# Aufruf:  tools/mark.sh "Heizung eco, Soll 18 °C (über HA)"
#          tools/mark.sh            → fragt den Text ab

set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p samples/raw

TEXT="${*:-}"
if [[ -z "$TEXT" ]]; then
  read -r -p "Aktion: " TEXT
fi

TS="$(date +%Y-%m-%dT%H:%M:%S%z)"
printf '%s\t%s\n' "$TS" "$TEXT" >> samples/raw/markers.tsv
echo "$TS  $TEXT"
