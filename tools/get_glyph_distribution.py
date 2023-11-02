from hyperglot.languages import Languages
from hyperglot.language import Language, Orthography

hg = Languages()
chars = {}

for iso, lang in hg.items():
    l = Language(lang, iso)
    try:
        primary = l.get_orthography(status="primary")
        o = Orthography(primary)
    except Exception as e:
        continue

    all = o.base_chars + o.base_marks + o.auxiliary_chars + o.auxiliary_marks

    for char in all:
        if char not in chars.keys():
            chars[char] = [1, l["speakers"]]
        else:
            chars[char][0] += 1
            chars[char][1] += l["speakers"]

combine = [(char, data[0], data[1]) for char, data in chars.items()]

print(sorted(combine, key=lambda tpl: tpl[1]))

# print([tpl[0] for tpl in sorted(combine, key=lambda tpl: tpl[1])])
with open("distribution.txt", "w") as file:
    file.write("\n".join([tpl[0] for tpl in sorted(combine, key=lambda tpl: tpl[1], reverse=True)]))
