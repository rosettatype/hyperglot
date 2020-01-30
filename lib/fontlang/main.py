import click
import os
import re
import yaml
import logging
from collections import OrderedDict
from fontTools.ttLib import TTFont
from . import __version__, DB, SCRIPTNAMES, SUPPORTLEVELS
from .languages import Languages, Language


def validate_font(ctx, param, value):
    """
    Validation method to ensure we can work with the passed in font file
    """
    for v in value:
        if os.path.splitext(v)[1][1:] not in ["ttf", "otf"]:
            raise click.BadParameter("The passed in font file does not appear to "
                                     "be of ttf or otf format")

        try:
            _font = TTFont(v, lazy=True)
            _font.close()
        except Exception as e:
            raise click.BadParameter("Could not convert TTFont from passed in "
                                     "font file (%s)" % str(e))

    return value


def language_list(langs, native=False, users=False, script=None, seperator=", "):
    """
    Return a printable string for all languages
    """
    items = []
    for iso, l in langs.items():
        lang = Language(l, iso)

        if native and script:
            name = lang.get_autonym(script)
        else:
            name = lang.get_name(script)

        if name is False:
            name = "(iso: %s)" % iso
            logging.info("No autonym found for language '%s'" % lang)
        else:
            name = re.sub(r"^\W*|\W*$", "", name)

        if users and "speakers" in l:
            items.append("%s (%s)" % (name, str(l["speakers"])))
        else:
            items.append("%s" % name)

    return seperator.join(items)


def print_to_cli(font, title, autonyms, users, script):
    print()
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()
    if "done" in font:
        done = font["done"]
        for script in done:
            count = len(done[script])
            if count > 0:
                print()
                title = "%d %s of %s script:" % \
                    (count, "language" if count == 1 else "languages",
                     SCRIPTNAMES[script])
                print(title)
                print("-" * len(title))
                print(language_list(done[script], autonyms, users, script))

    if "weak" in font:
        print()
        weak = font["weak"]
        for script in weak:
            count = len(weak[script])
            if count > 0:
                print()
                title = "There are %d %s of %s script that might be " \
                    "supported, but we cannot confirm it with our " \
                    "current database:" % \
                    (count, "langauage" if count == 1 else "languages",
                     SCRIPTNAMES[script])
                print(title)
                print("-" * len(title))
                print(language_list(weak[script], autonyms, users, script))


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
              )
@click.option("-a", "--autonyms", is_flag=True, default=False)
@click.option("-u", "--users", is_flag=True, default=False)
@click.option("-o", "--output", type=click.File(mode="w", encoding="utf-8"))
@click.option("-m", "--mode", type=click.Choice(MODES, case_sensitive=False),
              default=MODES[0], show_default=True)
@click.option("--include-historical", is_flag=True, default=False)
@click.option("--include-constructed", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-V", "--version", is_flag=True, default=False)
def cli(fonts, support, autonyms, users, output, mode, include_historical,
        include_constructed, verbose, version):

    if version:
        import sys
        sys.exit("Fontlang version: %s" % __version__)

    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.WARNING)
    """
    Main entry point for checking language support of a font binaries
    """
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
        Lang = Languages()
        langs = Lang.from_chars(chars, include_historical, include_constructed)
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
                # TODO add sort key from name/autonym
                if "todo_status" not in l or l["todo_status"] in done_statuses:
                    done[script][iso] = l
                else:
                    weak[script][iso] = l

        results[font] = {}

        if done:
            results[font]["done"] = done

        if weak:
            results[font]["weak"] = weak
        _font.close()

    if mode == "individual":
        for font in fonts:
            title = "%s has %s support for:" % (os.path.basename(font),
                                                level.lower())
            print_to_cli(results[font], title, autonyms, users, script)
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
        print_to_cli(union, title, autonyms, users, script)
        data = union

    elif mode == "intersection":
        print("intersection")
        intersection = results[fonts[0]]
        for font in fonts[1:]:
            res = results[font]

            intersection = prune_intersect(intersection, res, "done")
            intersection = prune_intersect(intersection, res, "weak")

        title = "Fonts %s all have common %s support for:" % \
            (", ".join([os.path.basename(f) for f in fonts]), level.lower())
        print_to_cli(intersection, title, autonyms, users, script)
        data = intersection

    if output:
        write_yaml(output, data)


def save_sorted():
    """
    Helper script to re-save the rosetta.yaml sorted alphabetically
    """
    logging.getLogger().setLevel(logging.DEBUG)
    Langs = Languages()

    # Sort by keys
    alphabetic = dict(OrderedDict(sorted(Langs.items())))

    file = open(DB, "w")
    yaml.dump(alphabetic, file, default_flow_style=False, allow_unicode=True)