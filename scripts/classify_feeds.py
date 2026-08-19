"""
Stuurt de ruwe artikellijst (raw_articles.json) naar de Claude API voor
classificatie per rubriek, en werkt daarna de FIFO-bestanden per rubriek
bij in data/feed-<rubriek-id>.json (maximaal 25 items per rubriek).

Dit is stap 2 van de wekelijkse workflow, direct na fetch_feeds.py.
"""

import json
import os
from pathlib import Path

import anthropic

from rubrieken import RUBRIEKEN, RUBRIEK_IDS
from weekhulp import huidige_week

RAW_FILE = Path(__file__).parent.parent / "raw_articles.json"
DATA_DIR = Path(__file__).parent.parent / "data"
WEEKARTIKELEN_DIR = DATA_DIR / "weekartikelen"
MAX_PER_RUBRIEK = 25
MODEL = "claude-haiku-4-5-20251001"


def bouw_prompt(artikelen):
    rubriek_tekst = "\n".join(
        f"- {r['id']}: {r['naam']} — {r['afbakening']}" for r in RUBRIEKEN
    )

    return f"""Je krijgt een lijst nieuwsartikelen van de afgelopen week. Verdeel ze over
de onderstaande rubrieken voor een aardrijkskunde-nieuwssite voor middelbare
scholieren.

RUBRIEKEN:
{rubriek_tekst}

REGELS:
- Kies per rubriek ongeveer 5 van de meest relevante en nieuwswaardige artikelen.
  Minder mag als het aanbod die week mager is; iets meer mag bij een rijke
  nieuwsweek. Verzin geen relevantie om toch aan 5 te komen.
- Vermijd bijna-identieke artikelen binnen dezelfde rubriek (streef naar
  diversiteit binnen de rubriek).
- Een artikel dat inhoudelijk sterk bij twee rubrieken hoort, mag in beide
  voorkomen. Doe dit alleen bij duidelijke overlap, niet bij een los raakvlak.
- Artikelen die bij geen enkele rubriek passen, laat je gewoon weg.
- Gebruik uitsluitend deze rubriek-ids in je antwoord: {", ".join(sorted(RUBRIEK_IDS))}

ARTIKELEN:
{json.dumps(artikelen, ensure_ascii=False)}

Antwoord UITSLUITEND met geldige JSON in dit exacte formaat, zonder uitleg of
markdown-opmaak eromheen:

[
  {{"titel": "...", "bron": "...", "url": "...", "datum": "YYYY-MM-DD", "rubrieken": ["rubriek-id"]}}
]
"""


def roep_llm_aan(artikelen):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    bericht = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": bouw_prompt(artikelen)}],
    )

    tekst = bericht.content[0].text.strip()

    # Vangnet voor het geval de LLM toch markdown-codefences toevoegt
    if tekst.startswith("```"):
        tekst = tekst.strip("`")
        if tekst.lower().startswith("json"):
            tekst = tekst[4:]
        tekst = tekst.strip()

    return json.loads(tekst)


def valideer(classificaties):
    """Filtert classificaties met ontbrekende velden of onbekende rubriek-ids eruit,
    zodat een rare LLM-afwijking nooit stilletjes een kapot databestand oplevert."""
    verplichte_velden = {"titel", "bron", "url", "datum", "rubrieken"}
    geldig = []

    for item in classificaties:
        if not verplichte_velden.issubset(item.keys()):
            print(f"Overgeslagen (velden ontbreken): {item}")
            continue

        onbekend = set(item["rubrieken"]) - RUBRIEK_IDS
        if onbekend:
            print(f"Onbekende rubriek-id(s) {onbekend} bij '{item['titel']}', overgeslagen.")
            continue

        geldig.append(item)

    return geldig


def werk_fifo_bij(classificaties):
    DATA_DIR.mkdir(exist_ok=True)

    per_rubriek = {r["id"]: [] for r in RUBRIEKEN}
    for item in classificaties:
        for rubriek_id in item["rubrieken"]:
            per_rubriek[rubriek_id].append({
                "titel": item["titel"],
                "bron": item["bron"],
                "url": item["url"],
                "datum": item["datum"],
            })

    for rubriek_id, nieuwe_items in per_rubriek.items():
        bestand = DATA_DIR / f"feed-{rubriek_id}.json"
        bestaand = json.loads(bestand.read_text(encoding="utf-8")) if bestand.exists() else []

        # Voorkom dubbele vermeldingen als eenzelfde artikel opnieuw wordt opgehaald
        nieuwe_urls = {a["url"] for a in nieuwe_items}
        bestaand = [a for a in bestaand if a["url"] not in nieuwe_urls]

        bijgewerkt = (nieuwe_items + bestaand)[:MAX_PER_RUBRIEK]

        bestand.write_text(
            json.dumps(bijgewerkt, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{rubriek_id}: {len(nieuwe_items)} nieuw toegevoegd, {len(bijgewerkt)} totaal in bestand")


def schrijf_weeksnapshot(classificaties):
    """Bewaart de volledige, geclassificeerde lijst van deze week apart —
    dit is de schone input die de opdrachten-workflow straks gebruikt om
    3 verhalen uit te kiezen, los van de opgeknipte FIFO-bestanden."""
    WEEKARTIKELEN_DIR.mkdir(parents=True, exist_ok=True)
    week = huidige_week()
    bestand = WEEKARTIKELEN_DIR / f"{week}.json"
    bestand.write_text(
        json.dumps(classificaties, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Weeksnapshot weggeschreven naar {bestand}")


def main():
    artikelen = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    print(f"{len(artikelen)} artikelen worden geclassificeerd door {MODEL}...")

    classificaties = roep_llm_aan(artikelen)
    classificaties = valideer(classificaties)
    print(f"{len(classificaties)} geldige classificaties ontvangen")

    schrijf_weeksnapshot(classificaties)
    werk_fifo_bij(classificaties)


if __name__ == "__main__":
    main()
