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
    SORTING,
    SORTING_DIRECTIONS,
    DB,
    SupportLevel,
    LanguageValidity,
    LanguageStatus,
    OrthographyStatus,
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

# Avoid saving yaml these files with 3 letter iso code in a way not supported
# on windows systems. They get "_" prefixed in lib/hyperglot/data
# See https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file#naming-conventions
ESCAPE_ISO_FILENAMES = ["con", "prn", "aux", "nul", "com", "lpt"]

RE_SPLIT = re.compile(r"[^A-z]+")


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


def validate_checks(ctx, param, value):
    return SupportLevel.parse(RE_SPLIT.split(value))


def validate_language_statuses(ctx, param, value):
    return LanguageStatus.parse(RE_SPLIT.split(value))


def validate_orthographies(ctx, param, value):
    return OrthographyStatus.parse(RE_SPLIT.split(value))


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
    millnames = ["", "k", "M", "B", "T"]
    n = float(n)
    millidx = max(
        0,
        min(
            len(millnames) - 1, int(math.floor(0 if n == 0 else math.log10(abs(n)) / 3))
        ),
    )

    return "{:.2f}{}".format(n / 10 ** (3 * millidx), millnames[millidx])


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
        print(
            "To see detailed language information (character set, speakers, autonym) use 'hyperglot-data \"Language Name or ISO code\"'"
        )
        print(
            "To see detailed check information use -v/-vv and the 'hyperglot-report' command"
        )
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
        "-c",
        "--check",
        default="base",
        show_default=True,
        callback=validate_checks,
        help=f"What to check support for. Options are '%s' or a comma-separated "
        "combination of those." % (", ".join(SupportLevel.values())),
    )
    @click.option(
        "--validity",
        type=click.Choice([v.value for v in LanguageValidity], case_sensitive=False),
        default=LanguageValidity.DRAFT.value,
        show_default=True,
        help="The level of validity for languages matched against the "
        "font. Weaker levels always include more strict levels. The "
        "default includes all languages for which the database has "
        "charset data. Options are one of '%s'"
        % (", ".join(LanguageValidity.values())),
    )
    @click.option(
        "-s",
        "--status",
        default=LanguageStatus.LIVING.value,
        show_default=True,
        callback=validate_language_statuses,
        help=f"Which languages to consider when checking support. Options are "
        "'%s' or a comma-separated combination of those."
        % (", ".join(LanguageStatus.values())),
    )
    @click.option(
        "-o",
        "--orthography",
        default=OrthographyStatus.PRIMARY.value,
        show_default=True,
        callback=validate_orthographies,
        help=f"Which orthographies to consider when checking support for a "
        "language. Options are '%s' or a comma-separated "
        "combination of those." % (", ".join(OrthographyStatus.values())),
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
        "-y",
        "--output",
        type=click.File(mode="w", encoding="utf-8"),
        help="Provide a name for a yaml file to write support " "information to.",
    )
    @click.option(
        "-t",
        "--shaping-threshold",
        default=0.01,
        type=click.FloatRange(0.0, 1.0, clamp=True),
        help="Complex script shaping checks pass when a font renders correctly "
        "for this frequency threshold. The frequency of "
        "combinations is highest for 1.0 (the most frequent combination) and "
        "converges to 0.0 the more rare a combination is. The default 0.01 "
        "requires all the most common combinations to be supported in the font.",
    )
    @click.option(
        "--no-shaping",
        is_flag=True,
        help="Disable shaping tests (mark attachment, joining behaviour, "
        "conjunct shaping)",
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
    check,
    validity,
    status,
    orthography,
    decomposed,
    marks,
    sorting,
    sort_dir,
    output,
    shaping_threshold,
    no_shaping,
    verbose,
    version,
    # Options not passed via Click, but only when forwarding the call
    # from hyperglot-reporter
    report_all=-1,
    report_missing=-1,
    report_joining=-1,
    report_conjuncts=-1,
    report_marks=-1,
):
    """
    Pass in one or more fonts to check their languages support.
    """

    if version:
        import sys

        sys.exit("Hyperglot version: %s" % __version__)

    if verbose == 1:
        loglevel = logging.INFO
    elif verbose > 1:
        # For debugging verbosity also opt in to all near misses reporting
        loglevel = logging.DEBUG
        logging.getLogger("hyperglot.checks.check_arabic_joining").setLevel(
            logging.DEBUG
        )
        logging.getLogger("hyperglot.checks.check_brahmi_conjuncts").setLevel(
            logging.DEBUG
        )
        logging.getLogger("hyperglot.checks.check_brahmi_halfforms").setLevel(
            logging.DEBUG
        )
        logging.getLogger("hyperglot.checks.check_combination_marks").setLevel(
            logging.DEBUG
        )
        logging.getLogger("hyperglot.checks.check_coverage").setLevel(logging.DEBUG)
        logging.getLogger("hyperglot.checks.check_mark_attachment").setLevel(
            logging.DEBUG
        )
        logging.getLogger("hyperglot.reporting.missing").setLevel(logging.WARNING)
        logging.getLogger("hyperglot.reporting.marks").setLevel(logging.WARNING)
        logging.getLogger("hyperglot.reporting.joining").setLevel(logging.WARNING)
        logging.getLogger("hyperglot.reporting.conjuncts").setLevel(logging.WARNING)
        report_missing = True
        report_joining = True
        report_marks = True
        report_conjuncts = True
    else:
        loglevel = logging.WARNING

        logging.getLogger("hyperglot.checks.check_arabic_joining").setLevel(loglevel)
        logging.getLogger("hyperglot.checks.check_brahmi_conjuncts").setLevel(loglevel)
        logging.getLogger("hyperglot.checks.check_brahmi_halfforms").setLevel(loglevel)
        logging.getLogger("hyperglot.checks.check_combination_marks").setLevel(loglevel)
        logging.getLogger("hyperglot.checks.check_coverage").setLevel(loglevel)
        logging.getLogger("hyperglot.checks.check_mark_attachment").setLevel(loglevel)
        
        # Disable reporting loggers by default
        logging.getLogger("hyperglot.reporting.missing").setLevel(logging.ERROR)
        logging.getLogger("hyperglot.reporting.marks").setLevel(logging.ERROR)
        logging.getLogger("hyperglot.reporting.joining").setLevel(logging.ERROR)
        logging.getLogger("hyperglot.reporting.conjuncts").setLevel(logging.ERROR)

    # Configure root logger with handler if not already configured
    if not logging.getLogger().handlers:
        if loglevel >= logging.WARNING:
            logging.basicConfig(level=loglevel, format="%(levelname)s: %(message)s")
        else:
            logging.basicConfig(
                level=loglevel, format="%(levelname)s (%(name)s): %(message)s"
            )
    else:
        logging.getLogger().setLevel(loglevel)
        # Also update handler levels to prevent INFO messages from showing
        for handler in logging.getLogger().handlers:
            handler.setLevel(loglevel)

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
    else:
        logging.getLogger("hyperglot.reporting.missing").setLevel(logging.ERROR)
    if report_marks >= 0:
        logging.getLogger("hyperglot.reporting.marks").setLevel(logging.WARNING)
    else:
        logging.getLogger("hyperglot.reporting.marks").setLevel(logging.ERROR)
    if report_joining >= 0:
        logging.getLogger("hyperglot.reporting.joining").setLevel(logging.WARNING)
    else:
        logging.getLogger("hyperglot.reporting.joining").setLevel(logging.ERROR)
    if report_conjuncts >= 0:
        logging.getLogger("hyperglot.reporting.conjuncts").setLevel(logging.WARNING)
    else:
        logging.getLogger("hyperglot.reporting.conjuncts").setLevel(logging.ERROR)

    log.info(
        "Performing language checks with these options: \n%s"
        % "\n".join(
            [
                f"fonts: {str(fonts)}",
                f"check: {str(check)}",
                f"validity: {str(validity)}",
                f"status: {str(status)}",
                f"orthography: {str(orthography)}",
                f"decomposed: {str(decomposed)}",
                f"marks: {str(marks)}",
                f"sorting: {str(sorting)}",
                f"sort_dir: {str(sort_dir)}",
                f"shaping_threshold: {str(shaping_threshold)}",
                f"no_shaping: {str(no_shaping)}",
            ]
        )
    )

    if fonts == ():
        print("Provide at least one path to a font or --help for more " "information")

    # A dict with each file and its results for each script
    results = {}

    for font_path in fonts:
        supported = FontChecker(font_path).get_supported_languages(
            check=check,
            validity=validity,
            status=status,
            orthography=orthography,
            decomposed=decomposed,
            marks=marks,
            shaping=(not no_shaping),
            shaping_threshold=shaping_threshold,
            report_missing=report_missing,
            report_marks=report_marks,
            report_joining=report_joining,
            report_conjuncts=report_conjuncts,
        )

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
        title = "%s has support for:" % (os.path.basename(font_path),)

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
def data(search=""):
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
@click.option(
    "--report-conjuncts",
    type=int,
    default=-1,
    help="TODO",
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
        and kwargs["report_conjuncts"] == -1
    ):
        print("No reporter option specified, reporting all issues (--report-all 0).")
        kwargs["report_all"] = 0

    # Simply call the main cli command with additional reporter arguments not
    # normally exposed to the user in the main cli command.
    ctx.forward(cli, **kwargs)
