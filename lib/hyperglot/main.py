import click
import os
import re
import yaml
import logging
import unicodedata2 as uni
from collections import OrderedDict
from fontTools.ttLib import TTFont
from . import __version__, DB, SUPPORTLEVELS, VALIDITYLEVELS
from .languages import Languages
from .language import Language
from .validate import validate
from .parse import (prune_superflous_marks,
                    parse_font_chars, parse_chars, parse_marks)

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


def language_list(langs, native=False, users=False, script=None,
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

        if users and "speakers" in l:
            items.append("%s (%s)" % (name, str(l["speakers"])))
        else:
            items.append("%s" % name)

    return seperator.join(items)


def print_to_cli(font, title, autonyms, users, strict_iso):
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()
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
                                autonyms, users, script, strict_iso))
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
                del(result[script][d])

        for d in delete_script:
            del(result[d])

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
              help="When set composable characters are not required as "
              "precomposed characters, but a font is valid if it has the "
              "required base and mark characters.")
@click.option("--validity", type=click.Choice(VALIDITYLEVELS,
                                              case_sensitive=False),
              default=VALIDITYLEVELS[1], show_default=True,
              help="The level of validity for languages matched against the "
              "font. Weaker levels always include more strict levels. The "
              "default includes all languages for which the database has "
              "charset data.")
@click.option("-a", "--autonyms", is_flag=True, default=False,
              help="Flag to render languages names in their native name.")
@click.option("-u", "--users", is_flag=True, default=False,
              help="Flag to show how many users each languages has.")
@click.option("-o", "--output", type=click.File(mode="w", encoding="utf-8"),
              help="Provide a name for a yaml file to write support "
              "information to.")
@click.option("-m", "--mode", type=click.Choice(MODES, case_sensitive=False),
              default=MODES[0], show_default=True,
              help="When passing in more than one file, a comparison can be "
              "generated. By default each file's support is listed "
              "individually. 'union' shows support for all languages "
              "supported by the combination of the passed in fonts. "
              "'intersection' shows the support all fonts have in common.")
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
def cli(fonts, support, decomposed, validity, autonyms, users, output, mode,
        include_all_orthographies, include_historical, include_constructed,
        strict_iso, verbose, version):
    """
    Pass in one or more fonts to check their languages support
    """

    if version:
        import sys
        sys.exit("Hyperglot version: %s" % __version__)

    log.setLevel(logging.DEBUG if verbose else logging.WARNING)
    if fonts == ():
        print("Provide at least one path to a font or --help for more "
              "information")

    # A dict with each file and its results for each script
    results = {}

    for font in fonts:
        chars = parse_font_chars(font)

        Lang = Languages(strict=strict_iso, prune=False)
        langs = Lang.get_support_from_chars(
            chars, support, validity, decomposed, include_all_orthographies,
            include_historical, include_constructed)
        level = SUPPORTLEVELS[support]
        results[font] = langs

    # Mode for comparison of several files
    if mode == "individual":
        for font in fonts:
            title = "%s has %s support for:" % (os.path.basename(font),
                                                level.lower())

            print_to_cli(results[font], title, autonyms, users, strict_iso)

        data = results
    elif mode == "union":
        union = union_results(*results.values())

        title = "Fonts %s combined have %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())

        print_to_cli(union, title, autonyms, users, strict_iso)

        # Wrap in "single file" 'union' top level, which will be removed when
        # writing the data
        data = {"union": union}

    elif mode == "intersection":
        intersection = intersect_results(*results.values())

        title = "Fonts %s all have common %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())

        print_to_cli(intersection, title, autonyms, users, strict_iso)

        # Wrap in "single file" 'intersection' top level, which will be removed
        # when writing the data
        data = {"intersection": intersection}

    if output:
        write_yaml(output, data)


def save_sorted(Langs=None, run_validation=True):
    """
    Helper script to re-save the hyperglot.yaml sorted alphabetically,
    alternatively from the passed in Langs object (which can have been
    modified)
    """
    log.setLevel(logging.WARNING)
    if Langs is None and run_validation is True:
        Langs = Languages(inherit=False, prune=False)
        print("Running pre-save validation, please fix any issues flagged.")
        validate()

    # Save with removed superflous marks
    for iso, lang in Langs.items():
        if "orthographies" in lang:
            for i, o in enumerate(lang["orthographies"]):
                for type in ["base", "auxiliary", "numerals"]:
                    if type in o:
                        chars = o[type]
                        pruned, removed = prune_superflous_marks(
                            " ".join(o[type]))

                        if len(removed) > 0:

                            log.info("Saving '%s' with '%s' pruned of "
                                     "superfluous marks (implicitly "
                                     "included in combining glyphs): "
                                     "%s"
                                     % (iso, type, "','".join(removed))
                                     )

                        chars = pruned

                        # Do not include anything (after decomposition)
                        # that is already listed in base
                        if "base" in o and type != "base":
                            chars = [
                                c for c in chars if c not in o["base"]]

                        joined = " ".join(chars)

                        Langs[iso]["orthographies"][i][type] = joined

                # Automate extracting and writing marks (in addition to any
                # that might have been defined manually). Note that we only
                # extract marks from 'base' since 'marks' are part of the
                # base level checking. Marks in 'auxiliary' will simply be
                # saved (if necessary) in 'auxiliary'.
                marks = []
                if "marks" in o:
                    marks = parse_chars(o["marks"],
                                        decompose=True,
                                        retainDecomposed=False)
                if "base" in o:
                    marks = set(marks + parse_marks(o["base"]))
                if len(marks) > 0:
                    # Note: Let's store marks with two spaces between to
                    # make them more legible; when parsing the attribute
                    # back in all whitespaces are removed
                    o["marks"] = "  ".join(sorted(marks))
                    if "base" in o:
                        base, removed = prune_superflous_marks(
                            " ".join(o["base"]))

                        # Save base without marks
                        _base = [c for c in base
                                 if not uni.category(c).startswith("M")]
                        o["base"] = " ".join(_base)

    # Sort by keys
    alphabetic = dict(OrderedDict(sorted(Langs.items())))

    file = open(DB, "w")
    yaml.dump(alphabetic, file, **DUMP_ARGS)
    print("Saved lib/hyperglot/hyperglot.yaml")


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
