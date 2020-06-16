import click
import os
import re
import yaml
import logging
from collections import OrderedDict
from fontTools.ttLib import TTFont
from . import __version__, DB, SUPPORTLEVELS
from .languages import Languages, Language


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


def language_list(langs, native=False, users=False, script=None, strict_iso=False,
                  seperator=", "):
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
            logging.info("No autonym found for language '%s'" % lang)
        else:
            # Trim whitespace and also 200E left to right marks, but allow ")"
            # as last character
            name = re.sub(r"^\W*|(?<=\))(\W*$)", "", name)

        if users and "speakers" in l:
            items.append("%s (%s)" % (name, str(l["speakers"])))
        else:
            items.append("%s" % name)

    return seperator.join(items)


def print_to_cli(font, title, autonyms, users, script, strict_iso):
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()
    if "done" in font:
        done = font["done"]
        total = 0
        for script in done:
            count = len(done[script])
            if count > 0:
                print()
                title = "%d %s of %s script:" % \
                    (count, "language" if count == 1 else "languages",
                     script)
                print(title)
                print("-" * len(title))
                print(language_list(done[script],
                                    autonyms, users, script, strict_iso))
                total = total + count
        if total > 0:
            print()
            print("%d languages supported in total." % total)
            print()

    if "weak" in font:
        print()
        weak = font["weak"]
        for script in weak:
            count = len(weak[script])
            if count > 0:
                print()
                title = "There are %d %s of %s script that are likely " \
                    "supported, but the database lacks independent " \
                    "confirmation:" % \
                    (count, "langauage" if count == 1 else "languages",
                     script)
                print(title)
                print("-" * len(title))
                print(language_list(weak[script],
                                    autonyms, users, script, strict_iso))


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
    yaml.dump(write, file, default_flow_style=False, allow_unicode=True)

    print()
    print("Wrote support information to %s" % file.name)


MODES = ["individual", "union", "intersection"]


@click.command()
@click.argument("fonts", type=click.Path(exists=True), callback=validate_font,
                nargs=-1)
@click.option("-s", "--support",
              type=click.Choice(SUPPORTLEVELS.keys(), case_sensitive=False),
              default="base", show_default=True,
              help="What level of language support to check the fonts for."
              )
@click.option("-a", "--autonyms", is_flag=True, default=False,
              help="Flag to render languages names in their native name.")
@click.option("-u", "--users", is_flag=True, default=False,
              help="Flag to show how many users each languages has.")
@click.option("-o", "--output", type=click.File(mode="w", encoding="utf-8"),
              help="Provide a name to a yaml file to write support "
              "information to.")
@click.option("-m", "--mode", type=click.Choice(MODES, case_sensitive=False),
              default=MODES[0], show_default=True,
              help="When checking more than one file, a comparison can be "
              "generated. By default each file's support is listed "
              "individually. 'union' shows support for all languages "
              "supported by the combination of the passed in fonts. "
              "'intersection' shows the support all files have in common.")
@click.option("--include-historical", is_flag=True, default=False,
              help="Flag to include otherwise ignored historical languages.")
@click.option("--include-constructed", is_flag=True, default=False,
              help="Flag to include otherwise ignored contructed languages.")
@click.option("--strict-support", is_flag=True, default=False,
              help="Flag to exclude language support data that has not "
              "undergone confirmation through several independend expert "
              "resources. All language data is carefully compiled from "
              "reliable sources and can be considered fairly reliable.")
@click.option("--strict-iso", is_flag=True, default=False,
              help="Flag to display names and macrolanguage data "
              "strictly abiding to ISO data. Without it apply some gentle "
              "transforms to show preferred languages names and "
              "macrolanguage structure that deviates from ISO data.")
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-V", "--version", is_flag=True, default=False)
def cli(fonts, support, autonyms, users, output, mode, include_historical,
        include_constructed, strict_support, strict_iso, verbose, version):
    """
    Pass in one or more fonts to check their languages support
    """

    if version:
        import sys
        sys.exit("Fontlang version: %s" % __version__)

    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.WARNING)
    if fonts == ():
        print("Provide at least one path to a font or --help for more "
              "information")

    # A dict with each file and its results for done and weak, e.g.
    # { 'filea.otf': { 'done': {..}, 'weak': {..} }, 'fileb.otf: .. }
    results = {}

    for font in fonts:
        _font = TTFont(font, lazy=True)
        cmap = _font["cmap"]
        chars = [chr(c) for c in cmap.getBestCmap().keys()]
        Lang = Languages(strict_iso)
        langs = Lang.get_support_from_chars(
            chars, include_historical, include_constructed)
        done = {}
        weak = {}
        done_statuses = ["done", "strong"]  # plus "status" not in dict
        level = SUPPORTLEVELS[support]

        # Sort the results for this font by db status
        for script in langs:
            if script not in done:
                done[script] = {}
            if script not in weak:
                weak[script] = {}

            if level not in langs[script]:
                continue
            for iso, l in langs[script][level].items():
                if "todo_status" not in l or l["todo_status"] in done_statuses:
                    done[script][iso] = l
                else:
                    weak[script][iso] = l

        results[font] = {}

        if strict_support:
            if done:
                results[font]["done"] = done

            if weak:
                results[font]["weak"] = weak
        else:
            merged = {}
            if done:
                merged = done
            if weak:
                if merged == {}:
                    merged = weak
                else:
                    for script, data in weak.items():
                        if script in merged:
                            merged[script].update(weak[script])
                        else:
                            merged[script] = weak[script]
            results[font]["done"] = merged
        _font.close()

    # Mode for comparison of several files
    if mode == "individual":
        for font in fonts:
            title = "%s has %s support for:" % (os.path.basename(font),
                                                level.lower())
            print_to_cli(results[font], title, autonyms,
                         users, script, strict_iso)
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
        print_to_cli(union, title, autonyms, users, script, strict_iso)
        # Wrap in "single file" 'union' top level, which will be removed when
        # writing the data
        data = {"union": union}

    elif mode == "intersection":
        print("intersection")
        intersection = results[fonts[0]]
        for font in fonts[1:]:
            res = results[font]

            intersection = prune_intersect(intersection, res, "done")
            intersection = prune_intersect(intersection, res, "weak")

        title = "Fonts %s all have common %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())
        print_to_cli(intersection, title, autonyms, users, script, strict_iso)
        # Wrap in "single file" 'intersection' top level, which will be removed
        # when writing the data
        data = {"intersection": intersection}

    if output:
        write_yaml(output, data)


def save_sorted(Langs=None):
    """
    Helper script to re-save the rosetta.yaml sorted alphabetically,
    alternatively from the passed in Langs object (which can have been
    modified)
    """
    logging.getLogger().setLevel(logging.WARNING)
    if Langs is None:
        Langs = Languages(inherit=False)

    # Sort by keys
    alphabetic = dict(OrderedDict(sorted(Langs.items())))

    file = open(DB, "w")
    yaml.dump(alphabetic, file, default_flow_style=False, allow_unicode=True)


@click.command()
@click.argument("output", type=click.Path())
def export(output):
    """
    Helper script to export rosetta.yaml with all inhereted orthographies
    expanded
    """
    logging.getLogger().setLevel(logging.WARNING)
    Langs = dict(Languages(inherit=True).items())

    file = open(output, "w")
    yaml.dump(Langs, file, default_flow_style=False, allow_unicode=True)
