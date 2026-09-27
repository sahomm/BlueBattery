#!/usr/bin/env bash
# Schneidet alle BlueBattery-Nachrichten und die HA-Discovery-Konfigurationen mit.
# Das Passwort wird verdeckt abgefragt und nirgends gespeichert.
#
# Aufruf:  tools/capture.sh <Sekunden> <Host> [Benutzer]
#          TOPICS='BlueBattery/# BB/#' tools/capture.sh 3600 192.168.1.10
# Ausgabe: samples/raw/capture_<Zeitstempel>.tsv  (Zeit, retained, Topic, Payload)
#
# Für Schalttests parallel in einem zweiten Terminal tools/mark.sh "<Aktion>"
# aufrufen; die Markierungen landen in samples/raw/markers.tsv.

set -euo pipefail

DURATION="${1:-120}"
HOST="${2:?Aufruf: tools/capture.sh <Sekunden> <Host> [Benutzer]}"
USER_NAME="${3:-mqtt_user}"
PORT=1883
# BB/# = Topics älterer Firmware, die noch retained im Broker liegen können
TOPICS="${TOPICS:-BlueBattery/# homeassistant/# BB/#}"

cd "$(dirname "$0")/.."
mkdir -p samples/raw
OUT="samples/raw/capture_$(date +%Y%m%d_%H%M%S).tsv"

TOPIC_ARGS=()
for t in $TOPICS; do TOPIC_ARGS+=(-t "$t"); done

read -r -s -p "MQTT-Passwort für ${USER_NAME}@${HOST}: " MQTT_PW
echo

echo "Schneide ${DURATION} s mit (${TOPICS}) → ${OUT}"
echo "Abbrechen jederzeit mit Strg+C – bis dahin Mitgeschnittenes bleibt erhalten."
mosquitto_sub -h "$HOST" -p "$PORT" -u "$USER_NAME" -P "$MQTT_PW" \
  -W "$DURATION" \
  -F '%I\t%r\t%t\t%p' \
  "${TOPIC_ARGS[@]}" \
  > "$OUT" || true   # -W beendet mit Exit-Code 27, Strg+C mit 130 – beides gewollt
unset MQTT_PW

echo "Fertig: $(wc -l < "$OUT") Zeilen, $(cut -f3 "$OUT" | sort -u | wc -l) Topics"
