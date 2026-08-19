"""Gedeelde hulpfunctie voor het weeknummer, zodat feeds- en opdrachten-scripts
altijd dezelfde week-notatie gebruiken (bv. '2026-W34')."""

from datetime import datetime, timezone


def huidige_week() -> str:
    iso = datetime.now(tz=timezone.utc).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"
