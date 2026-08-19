"""
Haalt nieuwsartikelen op uit de RSS-feeds in sources.json, filtert op de
afgelopen 7 dagen, schoont ze op en schrijft het resultaat weg naar
raw_articles.json.

Dit is stap 1 van de wekelijkse workflow:
  bronnen ophalen (dit bestand) -> classify_feeds.py -> data/feed-<rubriek>.json
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

SOURCES_FILE = Path(__file__).parent / "sources.json"
OUTPUT_FILE = Path(__file__).parent.parent / "raw_articles.json"
DAGEN_TERUGKIJKEN = 7


def strip_html(tekst: str) -> str:
    """Verwijdert eenvoudige HTML-tags uit een RSS-samenvatting."""
    schoon = re.sub(r"<[^>]+>", "", tekst or "")
    return re.sub(r"\s+", " ", schoon).strip()


def parse_datum(entry):
    """Haalt de publicatiedatum uit een feed-item, indien beschikbaar."""
    for veld in ("published_parsed", "updated_parsed"):
        tijd_struct = getattr(entry, veld, None)
        if tijd_struct:
            return datetime.fromtimestamp(time.mktime(tijd_struct), tz=timezone.utc)
    return None


def haal_bron_op(naam, url, grens):
    """Haalt en filtert artikelen van één RSS-bron. Faalt een bron, dan gaat
    het script gewoon door met de rest — één kapotte feed mag de hele run
    niet laten stoppen."""
    artikelen = []
    try:
        feed = feedparser.parse(url)
    except Exception as fout:
        print(f"  Kon {naam} niet ophalen: {fout}")
        return artikelen

    if feed.bozo and not feed.entries:
        print(f"  Feed van {naam} lijkt ongeldig, wordt overgeslagen.")
        return artikelen

    for entry in feed.entries:
        datum = parse_datum(entry)
        if datum is None or datum < grens:
            continue

        artikelen.append({
            "titel": strip_html(getattr(entry, "title", "")),
            "samenvatting": strip_html(getattr(entry, "summary", ""))[:400],
            "bron": naam,
            "url": getattr(entry, "link", ""),
            "datum": datum.date().isoformat(),
        })

    return artikelen


def dedupliceer(artikelen):
    """Verwijdert artikelen met een identieke URL (kan gebeuren als één bron
    meerdere feeds heeft die overlappen)."""
    gezien = set()
    uniek = []
    for a in artikelen:
        if a["url"] and a["url"] not in gezien:
            gezien.add(a["url"])
            uniek.append(a)
    return uniek


def main():
    bronnen = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    grens = datetime.now(tz=timezone.utc) - timedelta(days=DAGEN_TERUGKIJKEN)

    alle_artikelen = []
    for bron in bronnen:
        print(f"Ophalen: {bron['naam']}")
        artikelen = haal_bron_op(bron["naam"], bron["url"], grens)
        print(f"  {len(artikelen)} artikelen binnen de afgelopen {DAGEN_TERUGKIJKEN} dagen")
        alle_artikelen.extend(artikelen)

    alle_artikelen = dedupliceer(alle_artikelen)
    print(f"\nTotaal na deduplicatie: {len(alle_artikelen)} artikelen")

    OUTPUT_FILE.write_text(
        json.dumps(alle_artikelen, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Weggeschreven naar {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
