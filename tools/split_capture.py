#!/usr/bin/env python3
"""Zerlegt einen Mitschnitt von tools/capture.sh in eine Datei je Topic.

Aufruf:  tools/split_capture.py samples/raw/capture_<ts>.tsv
Ausgabe: samples/raw/<capture-name>/<topic>.json  (letzte Nachricht je Topic)
         samples/raw/<capture-name>/_index.tsv    (Topic, Anzahl, retained, JSON ja/nein)

Payloads können Zeilenumbrüche enthalten; ein neuer Datensatz beginnt immer
mit einem ISO-Zeitstempel.
"""

import json
import re
import sys
from pathlib import Path

RECORD_START = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\S*)\t([01])\t([^\t]*)\t", re.M)


def parse(text: str):
    matches = list(RECORD_START.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield m.group(1), m.group(2) == "1", m.group(3), text[m.end():end].rstrip("\n")


def main() -> None:
    src = Path(sys.argv[1])
    out = src.with_suffix("")
    out.mkdir(exist_ok=True)

    latest: dict[str, tuple[str, bool, str]] = {}
    counts: dict[str, int] = {}
    for ts, retained, topic, payload in parse(src.read_text(encoding="utf-8")):
        latest[topic] = (ts, retained, payload)
        counts[topic] = counts.get(topic, 0) + 1

    index = ["topic\tcount\tretained\tjson\tbytes"]
    for topic, (_ts, retained, payload) in sorted(latest.items()):
        try:
            data = json.loads(payload)
            body = json.dumps(data, indent=2, ensure_ascii=False)
            is_json = "ja"
        except ValueError:
            body = payload
            is_json = "nein"
        name = topic.replace("/", "__") or "_leer_"
        (out / f"{name}.json").write_text(body + "\n", encoding="utf-8")
        index.append(f"{topic}\t{counts[topic]}\t{int(retained)}\t{is_json}\t{len(payload)}")

    (out / "_index.tsv").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"{len(latest)} Topics → {out}")


if __name__ == "__main__":
    main()
