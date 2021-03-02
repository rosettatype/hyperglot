from hyperglot.languages import Languages
from hyperglot.main import save_sorted
from hyperglot.parse import character_list_from_string, list_unique

Langs = Languages(inherit=False, prune=False)

# TBD Coptic, Adlam, others?
bicameral = ["Latin", "Greek", "Cyrillic", "Georgian", "Armenian"]
for iso, lang in Langs.items():
    if "orthographies" in lang:
        for o in lang["orthographies"]:
            if o["script"] not in bicameral or "inherit" in o:
                continue

            for level in ["base", "aux"]:
                if level in o:
                    caps = []
                    chars = character_list_from_string(o[level])
                    if chars:
                        for c in chars:
                            uc = c.upper()
                            if c != uc:
                                if len(c) != len(uc):
                                    print("Skipping uppercase character that "
                                          "has different length, manually "
                                          "review (%s): %s %s"
                                          % (iso, c, uc))
                                else:
                                    caps.append(uc)
                        if caps:
                            o[level] = " ".join(list_unique(caps + chars))

save_sorted(Langs)
