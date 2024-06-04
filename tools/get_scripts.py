"""
Gather a list of all scripts currently in use in Hyperglot, e.g. for checking
all scripts have a ISO 15924 mapping in lib/extra_data/script-names.yaml
"""

from hyperglot.languages import Languages
from hyperglot.language import Language

scripts = []

for l in Languages():
    lang = Language(l)
    if "orthographies" not in lang:
        continue

    for o in lang["orthographies"]:
        scripts.append(o["script"])

print(sorted(set(scripts)))
