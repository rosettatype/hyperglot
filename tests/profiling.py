import cProfile
from hyperglot import Language, Languages
from hyperglot.cli import cli
from hyperglot.checker import FontChecker

with cProfile.Profile() as pr:
    # Languages()
    # Language("eng")
    # cli(("tests/Roboto/Roboto-Black.ttf",))
    FontChecker("tests/Roboto/Roboto-Black.ttf").get_supported_languages()
    pr.print_stats(sort="tottime")
    pr.dump_stats("tests/profile.prof")