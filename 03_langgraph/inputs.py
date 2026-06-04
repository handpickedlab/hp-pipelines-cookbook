"""Vaste casus-input — identiek aan README.md, gebruik dit bij elke run.

Niet aanpassen per framework: alleen het framework verandert, de input blijft gelijk.
"""

BRIEFING = (
    "Handpicked lanceert een interne tool waarmee agency-teams agent-pipelines "
    "kunnen hergebruiken in plaats van elke keer opnieuw te bouwen. We willen hier "
    "een LinkedIn-artikel over, gericht op B2B-marketeers en creatieve leads bij "
    "mid-size agencies. Doel: awareness plus een paar demo-aanvragen. We willen één "
    "concreet voorbeeld van een hergebruikte pipeline laten zien, en eindigen met een "
    "duidelijke call-to-action voor een demo. Het moet geloofwaardig en zelfverzekerd "
    "klinken, niet als marketinghype."
)

OUTPUT_PREFERENCES = {
    "format": "LinkedIn-artikel, markdown",
    "length_words": 600,
    "tone": "confident, technisch geloofwaardig, niet hypey, Nederlands",
    "structure": ["hook", "probleem", "oplossing met 1 concreet voorbeeld", "call-to-action"],
    "must_include": ["1 concreet voorbeeld", "1 call-to-action voor een demo"],
    "must_avoid": ["em-dashes", "revolutionair", "game-changer", "disruptief"],
}
