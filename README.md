# Rosetta’s database of languages

A database of languages and standard characters required for their representation.

This project started with a seemingly simple question: when can one claim that a font *F* supports a language *L*. This is needed for several reasons:

1. to organize and serve fonts to customers.
2. to better promote fonts with extensive langauge support.
3. to build character sets (and glyph sets) before development.
4. to test fonts, e.g. to heuristically create kerning pairs for consideration.
5. and probably quite a few reasons unrelated to typeface design.

A few notes to illustrate why the question of language support is complicated:

1. a single language can be written using different orthographies in one or more scripts.
2. languages are not isolated, there are loan word, names etc. from other languages.
3. what one person considers a dialect, is a language for someone else.
4. different kinds of texts require differnt vocabulary and hence different characters.

We have decided to take a pragmatic approach and reduce the problem to finding standard character set of each language (typically an official alphabet or syllabary or its approximation) and occassionally we provide a list of auxiliary characters used in reference literature (linguistics) or in very common loan words. In case the script used is bicameral, only lowercase versions of characters are provided with a few exceptions.

We are also providing a command-line tool to automate the analysis of language support

**This is a work in progress provided AS IS. If you want to contribute, do get in touch!**



## Database

The database is stored in the YAML file `hyperglot.yaml`.


### Languages

The highest level entries represent languages indexed using the ISO 639-3 code.

A brief note about a special kind of languages, first. [Macrolanguages](https://en.wikipedia.org/wiki/ISO_639_macrolanguage) are used by the ISO standard to keep ISO 639-2 and ISO 639-3 compatible in situations where one language entry was replaced by many. In this database macrolanguages group multiple individual languages. Most of them are not presented in any listings. The individual languages they contain are shown instead. However, in some situations, it is our preference to present some of the macrolanguages as if they were individual languages. This is mainly to simplify the listings or to deal with scarcity of information for the individual languages.

Each language entry can have these attributes which default to empty string or list unless stated otherwise:

- `name` (required): the English name of the language. This is also based on ISO 639-3. 
- `preferred_name` (optional): an override of the ISO 639-3 name. This is useful when the ISO 639-3 name  is pejorative or racist. We also use this to simplify very long names and where we have a preference (e.g. Sami over Saami).
- `autonym` (optional): the name of the language in the language itself.
- `orthographies` (optional): a list of orthographies for this language. They are described below. If missing, it is inherited from a parent macrolanguage if this exist.
- `includes` (optional) is used for macrolanguages only, contains a list of ISO 639-3 codes referring to the sub-languages of the macrolanguage. See below for a note about macrolanguages.
- `preferred_as_individual` (optional, defaults to: `false`), used for macrolanguages only: `true` or `false`, indicates that the macrolanguage will be presented exceptionally as single individual language. We use this when there are too many individual sub-languages with insufficient information.
- `speakers` (optional) is a number of L1 speakers obtained from Wikipedia. Note that this is a number of speakers, thus one needs to account for literacy rate in particular language. This can an integer or a range.
- `speakers_date` (optional) is the publication date of the reference used for the speakers count on Wikipedia.
- `status` (required, defaults to `living`) may be one of `historical, constructed, living`.
- `source` (optional) is a list of source names used to define the orthographies, e.g. Wikipedia, Omniglot, Alvestrand. See below for the complete list.
- `todo_status` (required, defaults to `todo`): one of `todo, done, confirmed` with the following meaning:
  - `todo` for unfinished entries which may be used to detect a potential language support with little certainty.
  - `done` for entries we have checked with at least two sources.
  - `confirmed` for entries confirmed by a native speaker or a linguist.
- `note` (optional): a note of any kind.

The attributes starting with `preferred_` are set according to our preference. They can be turned off when using the database via the CLI tool or module to strictly adhere to ISO 639-3.


### Orthographies

A language can refer to one or more orthographies. Macrolanguages *typically* do not refer to any. An orthography specifies the script and characters from this script used to represent the language. There can be multiple orthographies for the same language using the same script. Each orthographic entry can have these attributes which default to empty string or list unless stated otherwise:

- `required` (required): a string of characters or combinations of characters that are required to represent the language in common texts. This typically maps to a standard alphabet or syllabary for the language or am approximation of thereof.
- `auxiliary` (optional): a string of characters or combinations of characters that are not part of the standard alphabet, but appear in very common loan words or in reference literature. Deprecated characters can be included here too, e.g. `ş ţ` for Romanian.
- `numerals` (optional, defaults to `0123456789`): a string of numeric characters required for this language in this orthography.
- `autonym` (optional): the name of the language in the language itself using this orthography. If missing, the `autonym` defined in the parent language entry is used.
- `script` (required): a four-letter Unicode tag referring to a script of this orthography, e.g. Latn, Arab, Cyrl.
- `status` (required, defaults to `living`): one of: `deprecated, secondary, local, living`. The value `local` refers to an orthography which is used only is specific region.
- `note` (optional): a note of any kind.


### Example of individual language with one orthography

```
dan:
  orthographies:
  - base: a b c d e f g h i j k l m n o p q r s t u v w x y z å æ ø
    auxiliary: ǻ  # this character is used only in linguistic literature for Danish
    autonym: Dansk
    script: Latn
  name: Danish
  speakers: 6000000
  source: [Omniglot, Wikipedia, CLDR]
  todo_status: strong  # status of the database record
```


### Example of macrolanguage entry

```
fas:
  name: Persian
  includes: [pes, prs, tgk, aiq, bhh, haz, jpr, phv, deh, jdt, ttt]
  speakers: 70000000
  source: [Wikipedia]
```



## Command-line tool

A simple CLI tool is provided to output language support data for a passed in font file.


### Installation

Install via repo and pip:

```
$ pip install git+https://github.com/rosettatype/langs-db
```


### Usage

`$ fontlang path/to/font.otf`

or to check several fonts at once, or their combined coverage (with `-m union`)

`$ fontlang path/to/font.otf path/to/anotherfont.otf ...`

**Additional options**:

- `-s, --support`: Specify what level of support to check against (currently options are "base" (default if omitted) or "aux")
- `-a, --autonyms`: Output the language names in their native language and script
- `-u, --users`: Also output language user count (where available)
- `-o, --output`: Supply a file path to write the output to, in yaml format. For a single input font this will be a subset of rosetta.yaml with the languages and orthographies that the font supports. If several fonts are provided the yaml file will have a top level dict key for each file. If the `-m` option is provided the yaml file will contain the specific intersection or union result
- `-m, --mode`: How to process input if several files are provided (currently options are "individual", "union" and "intersection")
- `--include-historical`: option to include languages and orthographies marked as historical (default is False)
- `--include-constructed`: option to include languages and orthographies that are marked as constructed (default is False)
- `-v, --verbose`: More logging information (default is False)
- `-V, --version`: Print the version fontlang version number (default is False)


### Validating and sorting the database yaml file

Simple validation and sorting script to verify the data integrity of `data/rosetta.yaml` and point out possible formatting errors is included as `fontlang-validate` (prints problems to terminal) and `fontlang-save` (saves the rosetta.yaml sorted alphabetically by iso keys)


### Development

To run the script during development without having to constantly reinstall the pip package, you can use:

```
$ git clone git@bitbucket.org:rosettatype/fontlang.git && cd fontlang
$ pip install --upgrade --user --editable .
```

Additionally, to dynamically link the information in `data/rosetta.yaml` into the python package to be used, link them into the package:

```
$ rm lib/fontlang/rosetta.yaml
$ ln data/rosetta.yaml lib/fontlang/rosetta.yaml
```

It is `lib/fontlang/rosetta.yaml` that gets packages with the `fontlang` CLI command!


## Other databases included in this repo

The following are YAML files distilled from the original data stored in subfolders with corresponding names.

- `data/alvestrand.yaml` – data (indexed by ISO 639-3 codes) scraped from Alvestrand (see Sources below).
- `data/cldr.yaml` - data (indexed by 4-letter script tags and ISO 639-3 language codes) from Unicode’s CLDR database.
- `data/iso-639-3.yaml` – data from IS0 639-3 (three-letter codes) with corresponding ISO 639-2 (older three-letter codes) and ISO 639-1 (two-letter codes) where available. Also includes language names and attributes from ISO 639-3.
- `data/iso-639-3_retirements.yaml` – language codes no longer available in ISO 639-3
- `data/iso-639-2_collections.yaml` – language collections from ISO 639-2 (no longer available in ISO 639-3)
- `data/opentype-language-tags.yaml` –OpenType language tags and names with their corresponding ISO 639-3 language codes

The following data is not used or used only to build comparisons:

- `data/other/extensis` – character sets compiled by Extensis/WebINK
- `data/other/iana` – from [IANA language subtag registry](https://www.iana.org/assignments/lang-subtags-templates/lang-subtags-templates.xhtml)
- `data/other/latin-plus` - data from a [Latin-only database compiled by Underware](https://underware.nl/latin_plus/)


## Sources

The main sources we used to build the database are:

- [Unicode CLDR](http://unicode.org)
- [Wikipedia](http://wikipedia.org)
- [Omniglot](http://omniglot.com)
- Alvestrand, Harald Tveit. Characters and character sets for various languages. 1995.

The autonyms were sourced from Ethnologue, Wikipedia, and Omniglot (in this order preferrably). The speaker counts are from Wikipedia.


## Credits

This project is supported by [Rosetta Type Foundry](http://rosettatype.com).

- David Březina  
- Sergio Martins  
- Johannes Neumeier
- Toshi Omagari
