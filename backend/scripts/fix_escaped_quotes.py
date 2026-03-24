#!/usr/bin/env python3
"""Fix the 2 entries with escaped quotes that the main script missed."""
import pathlib

LOCALE = pathlib.Path(__file__).resolve().parent.parent / 'locale'

fixes_en = {
    'O que significa \\"Biobrassica\\"': 'What does \\"Biobrassica\\" mean',
    'O nome \\"Biobrassica\\" junta duas ideias que orientam tudo o que fazemos: Bio, pela agricultura biológica e por um modo de produção responsável, e brassica, em homenagem à família de hortícolas que simboliza a origem agrícola da nossa região.': 'The name \\"Biobrassica\\" brings together two ideas that guide everything we do: Bio, for organic farming and responsible production, and brassica, honouring the family of vegetables that symbolises the agricultural heritage of our region.',
}

fixes_fr = {
    'O que significa \\"Biobrassica\\"': 'Que signifie \\u00ab Biobrassica \\u00bb',
    'O nome \\"Biobrassica\\" junta duas ideias que orientam tudo o que fazemos: Bio, pela agricultura biológica e por um modo de produção responsável, e brassica, em homenagem à família de hortícolas que simboliza a origem agrícola da nossa região.': "Le nom \\\"Biobrassica\\\" réunit deux idées qui guident tout ce que nous faisons : Bio, pour l'agriculture biologique et un mode de production responsable, et brassica, en hommage à la famille de légumes qui symbolise l'origine agricole de notre région.",
}

fixes_pt = {
    'O que significa \\"Biobrassica\\"': 'O que significa \"Biobrassica\"',
    'O nome \\"Biobrassica\\" junta duas ideias que orientam tudo o que fazemos: Bio, pela agricultura biológica e por um modo de produção responsável, e brassica, em homenagem à família de hortícolas que simboliza a origem agrícola da nossa região.': 'O nome \"Biobrassica\" junta duas ideias que orientam tudo o que fazemos: Bio, pela agricultura biológica e por um modo de produção responsável, e brassica, em homenagem à família de hortícolas que simboliza a origem agrícola da nossa região.',
}

for lang, fixes in [('en', fixes_en), ('fr', fixes_fr), ('pt', fixes_pt)]:
    po = LOCALE / lang / 'LC_MESSAGES' / 'django.po'
    text = po.read_text()
    for msgid_val, msgstr_val in fixes.items():
        old = f'msgid "{msgid_val}"\nmsgstr ""'
        new = f'msgid "{msgid_val}"\nmsgstr "{msgstr_val}"'
        if old in text:
            text = text.replace(old, new)
            print(f'  [{lang}] Fixed: {msgid_val[:40]}...')
        else:
            print(f'  [{lang}] Already done or not found: {msgid_val[:40]}...')
    po.write_text(text)
