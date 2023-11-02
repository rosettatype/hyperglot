import click
import os
import re
import yaml
import logging
from collections import OrderedDict
from fontTools.ttLib import TTFont
from . import (__version__, SORTING_DIRECTIONS, DB, SUPPORTLEVELS,
               VALIDITYLEVELS, CHARACTER_ATTRIBUTES, MARK_BASE, SORTING)
from .languages import Languages, find_language
from .language import Language, Orthography, is_mark
from .validate import validate
from .parse import (list_unique, parse_font_chars, parse_marks)

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
    "width": 999
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
            raise click.BadParameter("The passed in font file does not appear "
                                     "to be of ttf or otf format")

        try:
            _font = TTFont(v, lazy=True)
            _font.close()
        except Exception as e:
            raise click.BadParameter("Could not convert TTFont from passed in "
                                     "font file (%s)" % str(e))

    return value


def language_list(langs, native=False, speakers=False, script=None,
                  strict_iso=False, seperator=", "):
    """
    Return a printable string for all languages
    """
    items = []
    for iso, l in langs.items():
        lang = Language(l, iso)

        if native and script:
            name = lang.get_autonym(script)
        else:
            name = lang.get_name(script, strict_iso)

        if name is False:
            name = "(iso: %s)" % iso
            log.info("No autonym found for language '%s'" % lang)
        else:
            # Trim whitespace and also 200E left to right marks, but allow ")"
            # as last character
            name = re.sub(r"^\W*|(?<=\))(\W*$)", "", name)

        if speakers and "speakers" in l:
            items.append("%s (%s)" % (name, str(l["speakers"])))
        else:
            items.append("%s" % name)

    return seperator.join(items)


def print_title(title):
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()


def print_to_cli(font, title, autonyms, speakers, strict_iso):
    print_title(title)
    total = 0
    for script in font:
        count = len(font[script])
        if count > 0:
            print()
            title = "%d %s of %s script:" % \
                (count, "language" if count == 1 else "languages",
                    script)
            print(title)
            print("-" * len(title))
            print(language_list(font[script],
                                autonyms, speakers, script, strict_iso))
            total = total + count
    if total > 0:
        print()
        print("%d languages supported in total." % total)
        print()


def intersect_results(*args):
    """
    Intersect any number of result dicts with script: { iso: lang } } input.
    Return the output ordered by script and iso.
    """

    if len(args) == 0:
        return {}

    result = args[0]
    for arg in args[1:]:
        delete_script = []
        for script in result.keys():
            delete_iso = []
            if script not in arg:
                delete_script.append(script)
                continue
            for iso, lang in result[script].items():
                if iso not in arg[script].keys():
                    delete_iso.append(iso)
            for d in delete_iso:
                del (result[script][d])

        for d in delete_script:
            del (result[d])

    return sorted_script_languages(result)


def union_results(*args):
    """
    Combine any number of results dicts with script: { iso: { lang } } input.
    Return the output ordered by script and iso.
    """
    result = {}
    for arg in args:
        for script, langs in arg.items():
            if script not in result:
                result[script] = langs
            else:
                for iso, lang in langs.items():
                    if iso not in result[script].keys():
                        result[script][iso] = lang
    return sorted_script_languages(result)


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
    Output of a CLI result into a yaml file.

    Transform the data into the same structure as the rosetta.yaml, e.g. with
    language iso top level keys only
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


MODES = ["individual", "union", "intersection"]


@click.command()
@click.argument("fonts", type=click.Path(exists=True), callback=validate_font,
                nargs=-1)
@click.option("-s", "--support",
              type=click.Choice(SUPPORTLEVELS.keys(), case_sensitive=False),
              default="base", show_default=True,
              help="Option to test only for the language's base charset, or to"
              " also test for presence of all auxilliary characters, if "
              "present in the database.")
@click.option("-d", "--decomposed", is_flag=True, default=False,
              help="When this option is set composable characters are not "
              "required as precomposed characters, but a font is valid if it "
              "has the required base and mark characters.")
@click.option("-m", "--marks", is_flag=True, default=False,
              help="When this option is set all combining marks for a "
              "language are required, not just precomposed encoded "
              "characters.")
@click.option("--validity", type=click.Choice(VALIDITYLEVELS,
                                              case_sensitive=False),
              default=VALIDITYLEVELS[1], show_default=True,
              help="The level of validity for languages matched against the "
              "font. Weaker levels always include more strict levels. The "
              "default includes all languages for which the database has "
              "charset data.")
@click.option("-a", "--autonyms", is_flag=True, default=False,
              help="Flag to render languages names in their native name.")
@click.option("--speakers", is_flag=True, default=False,
              help="Flag to show how many speakers each languages has.")
@click.option("--sort", "sorting",
              type=click.Choice(SORTING, case_sensitive=False),
              default="alphabetic", show_default=True)
@click.option("--sort-dir",
              type=click.Choice(SORTING_DIRECTIONS, case_sensitive=False),
              default=SORTING_DIRECTIONS[0], show_default=True)
@click.option("-o", "--output", type=click.File(mode="w", encoding="utf-8"),
              help="Provide a name for a yaml file to write support "
              "information to.")
@click.option("-c", "--comparison",
              type=click.Choice(MODES, case_sensitive=False),
              default=MODES[0], show_default=True,
              help="When passing in more than one file, a comparison can be "
              "generated. By default each file's support is listed "
              "individually. 'union' shows support for all languages "
              "supported by the combination of the passed in fonts. "
              "'intersection' shows the support all fonts have in common.")
@click.option("-l", "--languages", default="", 
              help="Pass in one or more comma-separated language names or ISO "
              "code to output a detailed support report for this font.")
@click.option("--include-all-orthographies", is_flag=True, default=False,
              help="Flag to show all otherwise ignored orthographies of a "
              "language.")
@click.option("--include-historical", is_flag=True, default=False,
              help="Flag to include otherwise ignored historical languages.")
@click.option("--include-constructed", is_flag=True, default=False,
              help="Flag to include otherwise ignored contructed languages.")
@click.option("--strict-iso", is_flag=True, default=False,
              help="Flag to display names and macrolanguage data "
              "strictly abiding to ISO data. Without it apply some gentle "
              "transforms to show preferred languages names and "
              "macrolanguage structure that deviates from ISO data.")
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-V", "--version", is_flag=True, default=False)
def cli(fonts, support, decomposed, marks, validity, autonyms, speakers,
        sorting, sort_dir,
        output, comparison,
        languages,
        include_all_orthographies, include_historical, include_constructed,
        strict_iso, verbose, version):
    """
    Pass in one or more fonts to check their languages support
    """

    if version:
        import sys
        sys.exit("Hyperglot version: %s" % __version__)

    loglevel = logging.DEBUG if verbose else logging.WARNING
    log.setLevel(loglevel)
    logging.getLogger("hyperglot.languages").setLevel(loglevel)
    logging.getLogger("hyperglot.language").setLevel(loglevel)
    if fonts == ():
        print("Provide at least one path to a font or --help for more "
              "information")

    # A dict with each file and its results for each script
    results = {}

    for font in fonts:
        chars = parse_font_chars(font)

        langs = Languages(strict=strict_iso)
        supported = langs.supported(chars, support, validity,
                                    decomposed, marks,
                                    include_all_orthographies,
                                    include_historical,
                                    include_constructed)
        level = SUPPORTLEVELS[support]

        # Sort each script's results by the chosen sorting logic
        sorted_entries = {}
        for script, entries in supported.items():
            sorted_entries[script] = sorted(entries.values(),
                                            key=SORTING[sorting],
                                            reverse=sort_dir.lower() != "asc")
            # Reformat as (ordered) dict with iso:info
            by_iso = {lang.iso: lang for lang in sorted_entries[script]}
            sorted_entries[script] = OrderedDict(by_iso)

        results[font] = sorted_entries

    # Mode for comparison of several files
    if comparison == "individual":
        for font in fonts:
            title = "%s has %s support for:" % (os.path.basename(font),
                                                level.lower())

            print_to_cli(results[font], title, autonyms, speakers, strict_iso)

        data = results
    elif comparison == "union":
        union = union_results(*results.values())

        title = "Fonts %s combined have %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())

        print_to_cli(union, title, autonyms, speakers, strict_iso)

        # Wrap in "single file" 'union' top level, which will be removed when
        # writing the data
        data = {"union": union}

    elif comparison == "intersection":
        intersection = intersect_results(*results.values())

        title = "Fonts %s all have common %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())

        print_to_cli(intersection, title, autonyms, speakers, strict_iso)

        # Wrap in "single file" 'intersection' top level, which will be removed
        # when writing the data
        data = {"intersection": intersection}

    if output:
        write_yaml(output, data)

    if languages:
        print_title("Language check:")
        languages = [l.strip() for l in languages.split(",") if l.strip() != ""]  # noqa

        for f in fonts:
            chars = parse_font_chars(f)
            for s in languages:
                res, _ = find_language(s)
                if res is False:
                    return
                for r in res:
                    res_name = r.get_name()
                    print(f"Listing full support information for {res_name}")
                    print()
                    if "orthographies" not in r:
                        continue
                    for o in r["orthographies"]:
                        ort = Orthography(o)
                        print(ort.diff(chars))


def save_sorted(Langs=None, run_validation=True):
    """
    Helper script to re-save the hyperglot.yaml sorted alphabetically,
    alternatively from the passed in Langs object (which can have been
    modified)
    """
    log.setLevel(logging.WARNING)
    if Langs is None and run_validation is True:
        Langs = Languages(inherit=False)
        print("Running pre-save validation, please fix any issues flagged.")
        validate()

    # Save with removed superflous marks
    for iso, lang in Langs.items():
        if "orthographies" in lang:

            whitespace = re.compile(r"\s+")

            for i, o in enumerate(lang["orthographies"]):

                # Automate extracting and writing marks (in addition to any
                # that might have been defined manually)
                marks = []
                if "marks" in o:
                    marks = parse_marks(o["marks"])

                # "Derive" all marks possible
                for attr in CHARACTER_ATTRIBUTES:
                    if attr in o:
                        marks = marks + parse_marks(o[attr])

                # Prune marks from character lists, delete empty
                for attr in CHARACTER_ATTRIBUTES:
                    if attr in o:
                        before = str(o[attr])
                        chars = [c.strip() for c in whitespace.split(o[attr])
                                 if not is_mark(c) and c != MARK_BASE]
                        if not chars:
                            log.warning("Removing attribute '%s' of '%s' - no "
                                        "characters left after normalization. "
                                        "Value was: '%s'" %
                                        (attr, iso, o[attr]))
                            del (o[attr])
                            continue

                        o[attr] = " ".join(chars)
                        if len(before) != len(o[attr]):
                            log.warning("Saving orthography attribute '%s' of "
                                        "'%s' changed its length. Whitespace "
                                        "or marks have been removed. "
                                        "\nBefore: '%s'\nAfter: '%s'" %
                                        (attr, iso, before, o[attr]))

                if len(marks) > 0:
                    # Note: Let's store marks with a dotted circle and a
                    # whitespace between them to make them more legible. When
                    # parsing the attribute back in circles and all whitespaces
                    # are removed
                    decorated = [MARK_BASE + m for m in list_unique(marks)]
                    o["marks"] = " ".join(decorated)

    # Ensure db folder exists
    if not os.path.isdir(DB):
        os.mkdir(DB)

    for iso, data in Langs.items():
        save_language(iso, data)

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
    logging.info(f"Saved lib/hyperglot/data/{iso}.yaml")


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
