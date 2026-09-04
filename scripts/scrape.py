#!/usr/bin/env python3
"""
Scraper titik panas (hotspot) BMKG Kaltim -> filter Kabupaten Berau.

Sumber data: https://kaltim.bmkg.go.id/api/koordinat-hotspot
Output:
  data/latest.json        -> snapshot terbaru (poin-poin hotspot di Berau saat ini)
  data/history.json       -> ringkasan harian (upsert per tanggal), untuk grafik tren
  data/history/<tanggal>.json -> arsip mentah poin per hari (opsional, untuk drill-down)

Dijalankan berkala oleh GitHub Actions (lihat .github/workflows/scrape.yml).
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

API_URL = "https://kaltim.bmkg.go.id/api/koordinat-hotspot"
KABUPATEN_TARGET = "BERAU"
WITA = timezone(timedelta(hours=8))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")
HISTORY_SUMMARY_PATH = os.path.join(DATA_DIR, "history.json")


def fetch_data(source_path=None):
    """Ambil data dari API BMKG. source_path dipakai untuk testing offline."""
    if source_path:
        with open(source_path, "r", encoding="utf-8") as f:
            return json.load(f)

    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; hotspot-berau-bot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def filter_berau(raw):
    points = raw.get("points", [])
    return [p for p in points if str(p.get("kabupaten", "")).strip().upper() == KABUPATEN_TARGET]


def summarize(points, tanggal):
    by_kecamatan = {}
    by_level = {}
    for p in points:
        kec = p.get("kecamatan", "TIDAK DIKETAHUI")
        lvl = p.get("levelName", p.get("level", "Tidak diketahui"))
        by_kecamatan[kec] = by_kecamatan.get(kec, 0) + 1
        by_level[lvl] = by_level.get(lvl, 0) + 1

    return {
        "date": tanggal,
        "total": len(points),
        "by_kecamatan": dict(sorted(by_kecamatan.items(), key=lambda kv: -kv[1])),
        "by_level": by_level,
    }


def load_json_or_default(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def upsert_history_summary(day_summary):
    history = load_json_or_default(HISTORY_SUMMARY_PATH, [])
    history = [h for h in history if h.get("date") != day_summary["date"]]
    history.append(day_summary)
    history.sort(key=lambda h: h["date"])
    with open(HISTORY_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return history


def main():
    source_path = sys.argv[1] if len(sys.argv) > 1 else None

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

    raw = fetch_data(source_path)
    berau_points = filter_berau(raw)

    now_wita = datetime.now(WITA)
    tanggal = raw.get("sourceDate")
    if tanggal and len(tanggal) == 8:
        tanggal = f"{tanggal[0:4]}-{tanggal[4:6]}-{tanggal[6:8]}"
    else:
        tanggal = now_wita.strftime("%Y-%m-%d")

    latest_payload = {
        "updatedAt": raw.get("updatedAt"),
        "scrapedAt": now_wita.isoformat(),
        "sourceDate": tanggal,
        "totalKaltim": raw.get("total", len(raw.get("points", []))),
        "totalBerau": len(berau_points),
        "points": berau_points,
    }
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump(latest_payload, f, ensure_ascii=False, indent=2)

    with open(os.path.join(HISTORY_DIR, f"{tanggal}.json"), "w", encoding="utf-8") as f:
        json.dump(berau_points, f, ensure_ascii=False, indent=2)

    day_summary = summarize(berau_points, tanggal)
    upsert_history_summary(day_summary)

    print(f"[OK] {tanggal}: {len(berau_points)} titik panas di Berau (dari {latest_payload['totalKaltim']} se-Kaltim)")


if __name__ == "__main__":
    main()
