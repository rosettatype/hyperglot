from hyperglot.checker import FontChecker
import click


@click.command()
@click.argument("font", type=click.Path(file_okay=True, dir_okay=False))
def main(font):
    checker = FontChecker(font)
    supported = []
    for script, langs in checker.get_supported_languages().items():
        for iso, lang in langs.items():
            if lang.speakers > 0:
                supported.append((lang, lang.speakers))
    supported.sort(key=lambda x: x[1], reverse=True)

    print("\nSorted by speaker count:")
    for lang, speakers in supported:
        print(f"{lang}: {speakers}")

    print()
    print("Total supported languages:", len(supported))
    print("Total speakers covered:", sum(speakers for _, speakers in supported))


if __name__ == "__main__":
    main()
