import click
import os
import re
import yaml
import logging
from collections import OrderedDict
from fontTools.ttLib import TTFont
from . import __version__, DB, SUPPORTLEVELS, VALIDITYLEVELS
from .languages import Languages
from .language import Language
from .parse import prune_superflous_marks, parse_font_chars

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


def prune_intersect(intersection, res, level):
    """
    Helper method to prune the intersection object against the res, which both
    may or may not have script keys with iso-to-language dicts

    Return intersection with only those dict values that are both in
    intersection and in res
    """
    if level in intersection:
        if level not in res:
            del(intersection[level])
        delete_script = []
        for script in intersection[level].keys():
            delete_iso = []
            if script not in res[level]:
                delete_script.append(script)
                continue
            for iso, lang in intersection[level][script].items():
                if iso not in res[level][script].keys():
                    delete_iso.append(iso)
            for d in delete_iso:
                del(intersection[level][script][d])

        for d in delete_script:
            del(intersection[level][d])

    return intersection


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
        for langs_by_status in results.values():
            for script, languages in langs_by_status.items():
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

        results[font] = {}
        results[font] = langs

    # Mode for comparison of several files
    if mode == "individual":
        for font in fonts:
            title = "%s has %s support for:" % (os.path.basename(font),
                                                level.lower())
            print_to_cli(results[font], title, autonyms, users, strict_iso)
        data = results
    elif mode == "union":
        union = {}
        for font in fonts:
            res = results[font]
            if "done" in res:
                if "done" not in union:
                    union["done"] = {}

            for iso, lang in res["done"].items():
                if iso not in union["done"]:
                    union["done"][iso] = lang

            if "weak" in res:
                if "weak" not in union:
                    union["weak"] = {}
            for iso, lang in res["weak"].items():
                if iso not in union["weak"]:
                    union["weak"][iso] = lang

        title = "Fonts %s together have %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())
        print_to_cli(union, title, autonyms, users, strict_iso)
        # Wrap in "single file" 'union' top level, which will be removed when
        # writing the data
        data = {"union": union}

    elif mode == "intersection":
        intersection = results[fonts[0]]
        for font in fonts[1:]:
            res = results[font]

            intersection = prune_intersect(intersection, res, "done")
            intersection = prune_intersect(intersection, res, "weak")

        title = "Fonts %s all have common %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())
        print_to_cli(intersection, title, autonyms, users, strict_iso)
        # Wrap in "single file" 'intersection' top level, which will be removed
        # when writing the data
        data = {"intersection": intersection}

    if output:
        write_yaml(output, data)


def save_sorted(Langs=None):
    """
    Helper script to re-save the hyperglot.yaml sorted alphabetically,
    alternatively from the passed in Langs object (which can have been
    modified)
    """
    log.setLevel(logging.WARNING)
    if Langs is None:
        Langs = Languages(inherit=False, prune=False)

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

                            if "base" in o and type != "base":
                                chars = [
                                    c for c in chars if c not in o["base"]]

                            joined = " ".join(chars)

                            Langs[iso]["orthographies"][i][type] = joined

    # Sort by keys
    alphabetic = dict(OrderedDict(sorted(Langs.items())))

    file = open(DB, "w")
    yaml.dump(alphabetic, file, **DUMP_ARGS)


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
