import click
import os
import re
import yaml
import math
import logging
import functools
from collections import OrderedDict
from fontTools.ttLib import TTFont
from hyperglot import (
    __version__,
    LANGUAGE_CACHE_FILE,
    SORTING_DIRECTIONS,
    DB,
    SupportLevel,
    LanguageValidity,
    SORTING,
)
from hyperglot.languages import Languages, find_language
from hyperglot.language import Language
from hyperglot.checker import FontChecker
from hyperglot.validate import validate_data

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

# All YAML dumps have these same additional arguments to make sure the unicode
# dumping and formatting is kosher.
DUMP_ARGS = {
    # Aka "make human readable"
    "default_flow_style": False,
    # D'ah
    "allow_unicode": True,
    # When dumping to yaml make sure not to intruduce line breaks in the
    # character lists (this will mess with the order in RTL strings).
    "width": 999,
}

# Avoid saving yaml files with 3 letter iso code in way not supported on
# windows systems.
# See https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file#naming-conventions
ESCAPE_ISO_FILENAMES = ["con", "prn", "aux", "nul", "com", "lpt"]


def validate_font(ctx, param, value):
    """
    Validation method to ensure we can work with the passed in font file
    """
    for v in value:
        if os.path.splitext(v)[1][1:] not in ["ttf", "otf"]:
            raise click.BadParameter(
                "The passed in font file does not appear " "to be of ttf or otf format"
            )

        try:
            _font = TTFont(v, lazy=True)
            _font.close()
        except Exception as e:
            raise click.BadParameter(
                "Could not convert TTFont from passed in " "font file (%s)" % str(e)
            )

    return value


def language_list(langs, script=None, seperator=", "):
    """
    Return a printable string for all languages
    """
    items = []
    for iso, l in langs.items():
        lang = Language(iso)

        name = lang.get_name(script)

        # Trim whitespace and also 200E left to right marks, but allow ")"
        # as last character
        name = re.sub(r"^\W*|(?<=\))(\W*$)", "", name)

        items.append("%s" % name)

    return seperator.join(items)



def millify(n):
    """
    Nicer human-readable rounded numbers (short scale!).
    Via https://stackoverflow.com/a/3155023/999162
    """
    millnames = ['','k','M','B','T']
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def print_title(title):
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()


def print_to_cli(font, title):
    print_title(title)
    total = 0
    speakers = 0
    for script in font:
        count = len(font[script])
        if count > 0:
            print()
            title = "%d %s of %s script:" % (
                count,
                "language" if count == 1 else "languages",
                script,
            )
            print(title)
            print("-" * len(title))
            print(language_list(font[script], script))
            total = total + count
            speakers += sum([l.speakers for l in font[script].values()])
    if total > 0:
        print()
        print("%d languages supported in total." % total)
        print("%s speakers in total." % millify(speakers))
        print()
        print()
        print("To see detailed information (character set, speakers, autonym) for a language use 'hyperglot-data \"Language Name or ISO code\"'")
        print()


def sorted_script_languages(obj):
    """
    Sort an input dictionary of script: { iso : {} } by script, first, and iso,
    second.
    """
    ordered = OrderedDict()
    if len(obj.keys()) == 0:
        return {}

    for script in sorted(obj.keys()):
        ordered[script] = OrderedDict()

        if len(obj[script].keys()) == 0:
            continue

        for iso in sorted(obj[script].keys()):
            ordered[script][iso] = obj[script][iso]

    return ordered


def write_yaml(file, data):
    """
    Output of a CLI result into a yaml file indexed by iso.
    """
    write = {}
    for path, results in data.items():
        # Use only the font's file name as index, not the entire path
        path = os.path.basename(path)
        for script, languages in results.items():
            if path not in write:
                write[path] = {}
            # Coerce l back  to dict from type Language
            languages = {iso: dict(l) for iso, l in languages.items()}
            write[path].update(languages)
    if len(data.keys()) == 1:
        # Single file input, write directly to top level by re-writing the
        # output dict without the filename level
        write = next(iter(write.values()))
    else:
        # Several file input, write path keys under which each file's support
        # results are listed
        # That's already how the data is :)
        pass
    yaml.dump(write, file, **DUMP_ARGS)

    print()
    print("Wrote support information to %s" % file.name)


def hyperglot_options(f):
    """
    Make the Click options for the main hyperglot command reusable, e.g. for
    the reporting command.
    """

    @click.argument(
        "fonts", type=click.Path(exists=True), callback=validate_font, nargs=-1
    )
    @click.option(
        "-s",
        "--support",
        type=click.Choice([s.value for s in SupportLevel], case_sensitive=False),
        default="base",
        show_default=True,
        help="Option to test only for the language's base charset, or to"
        " also test for presence of all auxilliary characters, if "
        "present in the database.",
    )
    @click.option(
        "-d",
        "--decomposed",
        is_flag=True,
        default=False,
        help="When this option is set composable characters are not "
        "required as precomposed characters, but a font is valid if it "
        "has the required base and mark characters.",
    )
    @click.option(
        "-m",
        "--marks",
        is_flag=True,
        default=False,
        help="When this option is set all combining marks for a "
        "language are required, not just precomposed encoded "
        "characters.",
    )
    @click.option(
        "--validity",
        type=click.Choice([v.value for v in LanguageValidity], case_sensitive=False),
        default=LanguageValidity.DRAFT.value,
        show_default=True,
        help="The level of validity for languages matched against the "
        "font. Weaker levels always include more strict levels. The "
        "default includes all languages for which the database has "
        "charset data.",
    )
    @click.option(
        "--sort",
        "sorting",
        type=click.Choice(SORTING, case_sensitive=False),
        default="alphabetic",
        show_default=True,
    )
    @click.option(
        "--sort-dir",
        type=click.Choice(SORTING_DIRECTIONS, case_sensitive=False),
        default=SORTING_DIRECTIONS[0],
        show_default=True,
    )
    @click.option(
        "-o",
        "--output",
        type=click.File(mode="w", encoding="utf-8"),
        help="Provide a name for a yaml file to write support " "information to.",
    )
    @click.option(
        "--include-all-orthographies",
        is_flag=True,
        default=False,
        help="Flag to show all otherwise ignored orthographies of a " "language.",
    )
    @click.option(
        "--include-historical",
        is_flag=True,
        default=False,
        help="Flag to include otherwise ignored historical languages.",
    )
    @click.option(
        "--include-constructed",
        is_flag=True,
        default=False,
        help="Flag to include otherwise ignored contructed languages.",
    )
    @click.option("-v", "--verbose", count=True)
    @click.option("-V", "--version", is_flag=True, default=False)
    @functools.wraps(f)
    def wrapper_hyperglot_options(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper_hyperglot_options


@click.command()
@hyperglot_options
def cli(
    fonts,
    support,
    decomposed,
    marks,
    validity,
    sorting,
    sort_dir,
    output,
    include_all_orthographies,
    include_historical,
    include_constructed,
    verbose,
    version,
    # Options not passed via Click, but only when forwarding the call
    # from hyperglot-reporter
    report_all=-1,
    report_missing=-1,
    report_joining=-1,
    report_marks=-1,
):
    """
    Pass in one or more fonts to check their languages support
    """

    if version:
        import sys

        sys.exit("Hyperglot version: %s" % __version__)

    if verbose == 1:
        loglevel = logging.INFO
    elif verbose > 1:
        # For debugging verbosity also opt in to all near misses reporting
        loglevel = logging.DEBUG
        logging.getLogger("hyperglot.reporting.marks").setLevel(logging.WARNING)
        logging.getLogger("hyperglot.reporting.joining").setLevel(logging.WARNING)
        report_missing = True
        report_joining = True
        report_marks = True
    else:
        loglevel = logging.WARNING

    log.setLevel(loglevel)
    logging.getLogger("hyperglot.languages").setLevel(loglevel)
    logging.getLogger("hyperglot.language").setLevel(loglevel)
    logging.getLogger("hyperglot.orthography").setLevel(loglevel)
    logging.getLogger("hyperglot.shaper").setLevel(loglevel)
    logging.getLogger("hyperglot.checker").setLevel(loglevel)

    # If the user wants more detailed output regarding near misses this is
    # achieved via this special logger

    # report_all sets all others, if set
    if report_all >= 0:
        report_missing = report_all
        report_marks = report_all
        report_joining = report_all

    if report_missing >= 0:
        logging.getLogger("hyperglot.reporting.missing").setLevel(logging.WARNING)
    if report_marks >= 0:
        logging.getLogger("hyperglot.reporting.marks").setLevel(logging.WARNING)
    if report_joining >= 0:
        logging.getLogger("hyperglot.reporting.joining").setLevel(logging.WARNING)

    if fonts == ():
        print("Provide at least one path to a font or --help for more " "information")

    # A dict with each file and its results for each script
    results = {}

    for font_path in fonts:
        supported = FontChecker(font_path).get_supported_languages(
            supportlevel=support,
            validity=validity,
            decomposed=decomposed,
            marks=marks,
            shaping=True,
            include_all_orthographies=include_all_orthographies,
            include_historical=include_historical,
            include_constructed=include_constructed,
            report_missing=report_missing,
            report_marks=report_marks,
            report_joining=report_joining,
        )

        level = SupportLevel(support).value

        # Sort each script's results by the chosen sorting logic
        sorted_entries = {}
        for script, entries in supported.items():
            sorted_entries[script] = sorted(
                entries.values(),
                key=SORTING[sorting],
                reverse=sort_dir.lower() != "asc",
            )
            # Reformat as (ordered) dict with iso:info
            by_iso = {lang.iso: lang for lang in sorted_entries[script]}
            sorted_entries[script] = OrderedDict(by_iso)

        results[font_path] = sorted_entries

    for font_path in fonts:
        title = "%s has %s support for:" % (
            os.path.basename(font_path),
            level.lower(),
        )

        print_to_cli(results[font_path], title)

    data = results

    if output:
        write_yaml(output, data)


def save_sorted(Langs: Languages = None, validate: bool = True) -> None:
    """
    Helper script to re-save the hyperglot.yaml sorted alphabetically,
    alternatively from the passed in Langs object (which can have been
    modified)
    """
    log.setLevel(logging.WARNING)
    
    try:
        os.remove(LANGUAGE_CACHE_FILE)
    except FileNotFoundError:
        pass

    if Langs is None and validate:
        Langs = Languages(inherit=False)
        print("Running pre-save validation, please fix any issues flagged.")
        validate_data()

    # Save with removed superflous marks
    for iso, lang in Langs.items():
        if "orthographies" in lang:
            for i, o in enumerate(lang["orthographies"]):
                lang["orthographies"][i] = o._get_raw()

    # Ensure db folder exists
    if not os.path.isdir(DB):
        os.mkdir(DB)

    for iso, data in Langs.items():
        save_language(iso, dict(data))

    print("Saved all language data to lib/hyperglot/data")


def save_language(iso, data):
    """
    Save the language data of one language by its three letter iso (mostly)
    """

    # Append underscore to escape file name for compliance with windows systems
    if iso in ESCAPE_ISO_FILENAMES:
        iso = f"{iso}_"

    file = open(os.path.join(DB, iso + ".yaml"), "w")
    yaml.dump(data, file, **DUMP_ARGS)
    log.info(f"Saved lib/hyperglot/data/{iso}.yaml")


@click.command()
@click.argument("output", type=click.Path())
def export(output):
    """
    Helper script to export hyperglot.yaml with all inhereted orthographies
    expanded
    """
    log.setLevel(logging.WARNING)
    Langs = dict(Languages(inherit=True).items())

    file = open(output, "w")
    yaml.dump(Langs, file, **DUMP_ARGS)


@click.command()
@click.argument("search")
def data(search):
    """
    Pass in a 3-letter iso code or language name (search term) to show
    Hyperglot data for it
    """
    print()
    print_title(f"Hyperglot data for '{search}':")

    search = search.lower().strip()

    hits, msg = find_language(search)

    print(msg)
    for h in hits:
        print(h.presentation)


@click.command()
@hyperglot_options
@click.option(
    "--report-all",
    type=int,
    default=-1,
    help="Parameter to set/overwrite all other --report-xxx parameters.",
)
@click.option(
    "--report-missing",
    type=int,
    default=-1,
    help="Parameter to report unmatched languages which are missing "
    "n or less characters. If n is 0 all languages with any number "
    "of missing characters are listed (default).",
)
@click.option(
    "--report-marks",
    type=int,
    default=-1,
    help="Parameter to report languages which are missing n or less "
    "mark attachment sequences. If n is 0 all languages with any "
    "number any number of missing mark attachment sequences "
    "are listed (default).",
)
@click.option(
    "--report-joining",
    type=int,
    default=-1,
    help="Parameter to report languages which are missing n or less "
    "joining sequences. If n is 0 all languages with any number of "
    "missing joining sequences are listed (default).",
)
@click.pass_context
def report(ctx, **kwargs):
    """Reporter command to get a list of missing character and shaping
    information for languages that the font does not support.
    """

    if (
        kwargs["report_all"] == -1
        and kwargs["report_missing"] == -1
        and kwargs["report_marks"] == -1
        and kwargs["report_joining"] == -1
    ):
        print("No reporter option specified, reporting all issues (--report-all 0).")
        kwargs["report_all"] = 0

    # Simply call the main cli command with additional reporter arguments not
    # normally exposed to the user in the main cli command.
    ctx.forward(cli, **kwargs)
