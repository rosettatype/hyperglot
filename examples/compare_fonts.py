"""
Use Hyperglot to compare several fonts.

Output a list of all scripts/languages:
- covered by the fonts combined (union)
- supported by all fonts (intersect)
"""
from hyperglot.checker import FontChecker
import click

@click.command()
@click.argument("fonts", nargs=-1, type=click.Path(file_okay=True, dir_okay=False))
def main(fonts):
    union = {}
    intersect = {}

    for path in fonts:

        # Use options as desired, see checker.py:Checker.get_supported_languages for all options
        support = FontChecker(path).get_supported_languages()

        # The returned support object for each font looks like this:
        # Script: { iso: Language, iso: Language}, so e.g.
        # Latin: { eng: Language English, fin: Language Finnish }, Arabic: {...}, ...

        # Join all scripts and all languages supported in any of the fonts:
        if union == {}:
            union = support
        else:
            for script, languages in support.items():
                if script not in union.keys():
                    union[script] = languages
                else:
                    for iso, l in languages.items():
                        if iso not in union[script].keys():
                            union[script][iso] = l

        # Keep only scripts and languages supported in all fonts:
        if intersect == {}:
            intersect = support
        else:
            pruned = dict(intersect)
            for script, languages in intersect.items():
                if script in support:
                    pruned[script] = {}
                else:
                    continue

                for iso in languages.keys():
                    if iso in support[script].keys():
                        pruned[script][iso] = intersect[script][iso]
            intersect = pruned
        
    print()
    print("The fonts combined cover a total of %d languages in %d scripts: \n%s" %
            (sum([len(l) for l in union.values()]), len(union.keys()), union))
    print()
    print("All of these fonts cover these %d language in %d scripts: \n%s" %
            (sum([len(l) for l in intersect.values()]), len(intersect.keys()), intersect))
    print()

if __name__ == "__main__":
    main()