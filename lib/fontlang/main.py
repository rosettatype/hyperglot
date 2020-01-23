import click
import os
import logging
import yaml
import re
from fontTools.ttLib import TTFont
from .Languages import Languages, Language, SCRIPTNAMES, SUPPORTLEVELS


def validate_font(ctx, param, value):
    """
    Validation method to ensure we can work with the passed in font file
    """
    if os.path.splitext(value)[1][1:] not in ["ttf", "otf"]:
        raise click.BadParameter("The passed in font file does not appear to "
                                 "be of ttf or otf format")

    try:
        _font = TTFont(value, lazy=True)
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
        l["iso"] = iso
        lang = Language(l)

        if native and script:
            name = lang.get_autonym(script)
        else:
            name = lang.get_name(script)

        if name is False:
            name = "(iso: %s)" % iso

        if users and "speakers" in l:
            items.append("%s (%s)" % (name, str(l["speakers"])))
            continue

        items.append("%s" % name)

    return seperator.join(items)


def write_yaml(file, data):
    """
    Output of a CLI result into a yaml file.

    For now no data-transformation performed
    """
    yaml.dump(data, file, default_flow_style=False, allow_unicode=True)


@click.command()
@click.argument("font", type=click.Path(exists=True), callback=validate_font)
@click.option("-s", "--support",
              type=click.Choice(SUPPORTLEVELS.keys(), case_sensitive=False),
              default="base", show_default=True,
              )
@click.option("-a", "--autonyms", is_flag=True, default=False)
@click.option("-u", "--users", is_flag=True, default=False)
@click.option("-o", "--output", type=click.File(mode="w", encoding="utf-8"))
# TODO Implement --include-historical flag
# TODO Implement --log-level flag
def cli(font, support, autonyms, users, output):
    """
    Main entry point for checking language support of a font binary
    """
    _font = TTFont(font, lazy=True)
    cmap = _font["cmap"]
    chars = [chr(c) for c in cmap.getBestCmap().keys()]
    Lang = Languages()
    langs = Lang.from_chars(chars, )
    done = {}
    weak = {}
    done_statuses = ["done", "strong"]  # plus "status" not in dict
    level = SUPPORTLEVELS[support]

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

    print()
    print("%s has %s support for:" % (os.path.basename(font),
                                      level.lower()))

    if done:
        for script in done:
            count = len(done[script])
            if count > 0:
                print()
                print("%d %s of %s script:" %
                      (count, "language" if count == 1 else "languages",
                       SCRIPTNAMES[script]))
                print(language_list(done[script], autonyms, users, script))

    if weak:
        for script in weak:
            count = len(weak[script])
            if count > 0:
                print()
                print("There are %d %s of %s script that might be "
                      "supported, but we cannot confirm it with our current "
                      "database:" %
                      (count, "langauage" if count == 1 else "languages",
                       SCRIPTNAMES[script]))
                print(language_list(weak[script], autonyms, users, script))

    if output:
        write_yaml(output, done)

    _font.close()
