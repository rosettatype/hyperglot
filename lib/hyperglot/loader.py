import os
import yaml
import logging
from functools import lru_cache
from copy import deepcopy

from hyperglot import DB, DB_EXTRA

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


DATA_CACHE = {}

def load_language_data(iso: str) -> dict:
    """
    Load and cache the raw yaml data for a iso code. Always return deepcopies
    of the originally loaded data to avoid mutations down the road messing
    with new language objects.
    """

    if iso in DATA_CACHE:
        return deepcopy(DATA_CACHE[iso])

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

    DATA_CACHE[iso] = data

    return deepcopy(data)


@lru_cache
def load_scripts_data():
    with open(os.path.join(DB_EXTRA, "script-names.yaml"), "rb") as f:
        return yaml.load(f, Loader=yaml.Loader)


@lru_cache
def load_joining_types():
    """
    Load the joining-types.yaml database.

    TODO: Maybe this should be a singleton as well, or accessed transparently
    via Orthography?
    """
    with open(os.path.join(DB_EXTRA, "joining-types.yaml"), "rb") as f:
        return yaml.load(f, Loader=yaml.Loader)
