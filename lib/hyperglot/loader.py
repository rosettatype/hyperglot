import os
import yaml
import logging
from functools import lru_cache
from copy import deepcopy

from hyperglot import DB, DB_EXTRA

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

CACHE = {}


def cached_loader(func):
    """
    Load and cache the raw yaml data for a iso code. Always return deepcopies
    of the originally loaded data to avoid mutations down the road messing
    with new language objects.
    """

    def inner(path):

        if path in CACHE.keys():
            return deepcopy(CACHE[path])

        CACHE[path] = func(path)

        return deepcopy(CACHE[path])

    return inner


@cached_loader
def load_cached_yaml(path):
    with open(path, "rb") as f:
        return yaml.load(f, Loader=yaml.Loader)


def load_language_data(iso: str) -> dict:

    files = [f"{iso}.yaml", f"{iso}_.yaml", f"{iso}.yml", f"{iso}_.yml"]
    file = None
    path = None

    while len(files):
        file = files.pop(0)

        # The one place where the default.yaml will get injected to provide
        # data for a Language(iso=default) object
        if iso == "default":
            path = os.path.join(DB_EXTRA, file)
        else:
            path = os.path.join(DB, file)

        if os.path.isfile(path):
            break

        file = None
        path = None

    if path is None:
        log.debug(f"Attempted to load '{path}' for iso '{iso}'")
        raise KeyError(f"No language with ISO code {iso} found in Hyperglot.")

    return load_cached_yaml(path)


@lru_cache
def load_scripts_data():
    """
    Potentially called _a lot_, so lru_cache the result.
    """
    return load_cached_yaml(os.path.join(DB_EXTRA, "script-names.yaml"))


@lru_cache
def load_joining_types():
    """
    Potentially called _a lot_ (like for every character of all orthographies),
    so lru_cache the result.
    """
    return load_cached_yaml(os.path.join(DB_EXTRA, "joining-types.yaml"))
