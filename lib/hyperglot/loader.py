import os
import yaml
import logging
from copy import deepcopy

from hyperglot import DB

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


# This is the most expensive, so make sure any results are explicitly cached.
RAW_DATA_CACHE = {}

def load_language_data(iso: str) -> dict:
    """
    Load and cache the raw yaml data for a iso code. Always return deepcopies
    of the originally loaded data to avoid mutations down the road messing
    with new language objects.
    """

    if iso in RAW_DATA_CACHE:
        return deepcopy(RAW_DATA_CACHE[iso])
    
    files = [f"{iso}.yaml", f"{iso}_.yaml"]
    file = None
    path = None

    while len(files):
        file = files.pop(0)
        path = os.path.join(DB, file)
        if os.path.isfile(path):
            break
        file = None
        path = None

    if path is None:
        raise KeyError(f"No language with ISO code {iso} found in Hyperglot.")

    with open(path, "rb") as f:
        data = yaml.load(f, Loader=yaml.Loader)

    RAW_DATA_CACHE[iso] = data

    return deepcopy(data)
