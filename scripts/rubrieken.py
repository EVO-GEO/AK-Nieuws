"""
Centrale definitie van de vijf AK-Nieuws rubrieken.
Wordt gebruikt door de classificatiestap (feeds) en later ook de
opdrachten-workflow, zodat beide dezelfde rubriek-ids en afbakeningen
hanteren als de frontend (index.html).
"""

RUBRIEKEN = [
    {
        "id": "klimaat-water",
        "naam": "Klimaat & water",
        "afbakening": (
            "Weersextremen, klimaatverandering en de gevolgen daarvan, "
            "overstromingen, droogte, waterbeheer/dijken, zeespiegelstijging."
        ),
    },
    {
        "id": "energie-grondstoffen",
        "naam": "Energie & grondstoffen",
        "afbakening": (
            "Fossiele brandstoffen (olie, gas, kolen), mijnbouw en delfstoffen, "
            "energietransitie, windmolens/zonnepanelen, energieprijzen en -zekerheid."
        ),
    },
    {
        "id": "bevolking-wonen",
        "naam": "Bevolking & wonen",
        "afbakening": (
            "Verstedelijking, bevolkingsgroei/-krimp, woningnood, steden vs. platteland, "
            "migratie als ruimtelijk/demografisch proces (NIET de politieke/conflict-kant "
            "daarvan — die hoort bij 'Grenzen & identiteit')."
        ),
    },
    {
        "id": "arm-rijk",
        "naam": "Arm & rijk",
        "afbakening": (
            "Ontwikkeling(sverschillen), armoede en welvaart, internationale handel, "
            "globalisering, ontwikkelingshulp, economische groei van landen."
        ),
    },
    {
        "id": "grenzen-identiteit",
        "naam": "Grenzen & identiteit",
        "afbakening": (
            "Landsgrenzen en grensconflicten, oorlogen/spanningen tussen of binnen landen, "
            "cultuur en taal als identiteitskwestie, vluchtelingen door conflict "
            "(i.t.t. de ruimtelijke kant in 'Bevolking & wonen')."
        ),
    },
]

RUBRIEK_IDS = {r["id"] for r in RUBRIEKEN}
