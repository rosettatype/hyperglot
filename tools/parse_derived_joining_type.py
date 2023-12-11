"""
Parse the raw unicode dumped data txt file into a yaml dict for easier later
access. This would need to be done again for each Unicode version (assuming
there are changed or new joining character types)
"""
import re
import yaml
from hyperglot.main import DUMP_ARGS

source = "other/DerivedJoiningType.txt"
output = "lib/hyperglot/extra_data/joining-types.yaml"

joining_types = {}

with open(source, "r") as file:
    text = file.read()

# Remove comment lines
text = re.sub(r"^#.*", "\n", text, flags=re.MULTILINE)

# Remove empty lines
text = re.sub(r"\n+", "\n", text, flags=re.MULTILINE)

# Split into lines
lines = re.split(r"\n", text.strip())


for line in lines:
    # Of a line like:
    # 0640          ; C # Lm       ARABIC TATWEEL
    # 0883..0885    ; C # Lo   [3] ARABIC TATWEEL WITH OVERSTRUCK HAMZA..ARABIC TATWEEL WITH TWO DOTS BELOW
    # parse the unicode "0640" and the "C" joining type
    # note the possible "0883..0885" range of unicodes
    matches = re.findall(r"^([0-9A-F]{4,5})(?:\.{2})?([0-9A-F]{4,5})?\s+;\s([A-Z]{1})", line)
    uni_min = int(matches[0][0], 16)
    
    if matches[0][1] == "":
        joining_types[chr(uni_min)] = matches[0][2]
    else:
        uni_max = int(matches[0][1], 16)
        for uni in range(uni_min, uni_max):
            joining_types[chr(uni)] = matches[0][2]

with open(output, "w") as out:
    yaml.dump(joining_types, out, **DUMP_ARGS)
