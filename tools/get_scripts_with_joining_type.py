"""
Read the joining-types.yaml extra_data file and compile a list of all
unicodedata scripts that the character keys belong to; omit joining type "T"
(transparent) which is primarily combining marks and other controls cars, 
e.g. only list script which have listed joining types D, R, L, and require 
joining behavior.
"""

import os
import yaml
from fontTools.unicodedata import script

extra_data = os.path.join(
    os.path.dirname(__file__), "..", "lib", "hyperglot", "extra_data",
    "joining-types.yaml"
)

with open(extra_data, "r") as f:
    data = yaml.safe_load(f)

scripts = set()
for char, joining_type in data.items():
    if len(char) == 1 and joining_type != "T":
        scripts.add(script(ord(char)))

for s in sorted(scripts):
    print(s)
