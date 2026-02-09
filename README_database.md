# Database and contributing

The database is stored in the YAML file `lib/Hyperglot/data/xxx.yaml`.

## Languages

The highest level entries in the database represent languages indexed using their three-letter ISO 639-3 code.\* Each language entry can have the following attributes:

- `name` (required): the English name of the language. This is also based on ISO 639-3.
- `preferred_name` (optional): an override of the ISO 639-3 name. This is useful when the ISO 639-3 name is pejorative or racist. We also use this to simplify very long names and where we have a preference (e.g. Sami over Saami). This can be turned off when using the database via the CLI tool or module to adhere strictly to the naming as defined in ISO 639-3.
- `autonym` (optional): the name of the language in the language itself.
- `orthographies` (optional): a list of orthographies for the language. See orthography entry format below.
- `speakers` (optional) is a number of L1 speakers. Note that this is a number of speakers, not a number of readers. Only integer values are allowed. If a source lists a range the maximimum of the estimated range is listed.
- `speakers_date` (optional) is the publication date of the source used for the speakers count.
- `status` (required, defaults to `living`) one of the following:
  - `living`: a language that is currently in use and has some first-language (L1) speakers,
  - `historical: a language with no first-language (L1) speakers, or
  - `constructed`: a language that has been deliberately created, such as Esperanto or Interlingue.
- `sources` (required) a list of source references used to format the data. Please, read the [Criteria for establishing orthographies](#criteria-for-establishing-orthographies) and use APA style to format them.
- `validity` (required, defaults to `todo`): one of the following:
  - `todo` – an entry that is a work in progress,
  - `draft`: a complete entry that has not yet been sufficiently verified,
  - `preliminary`: a complete entry that has been verified using two online sources, or
  - `verified`: a complete entry that has been verified by a competent reviewer or by two authoritative sources.
- `note` (optional): a note of any kind
- `contributors` (optinal, recommended): a list of contributors for this file. Typically, a contributor would be a person using sources to provide valid data rather their own knowledge of the language.
- `reviewers` (optional): a reviewer is typically a competent speaker or a linguist, essentially a contributor that vouches, at the time of their edit, for the data validity with their own expertise. A person is either a contributor or a reviewer.

Unless stated otherwise above, the default values are either an empty string or an empty list.

\* We are aware that opinions regarding what constitutes a dialect or language differ, but we have to adhere to an international standard.

## Orthographies

A language can refer to one or more orthographies. An orthography specifies the script and characters from this script used to represent the language. There can be multiple orthographies for the same language using the same or different scripts. Each entry can have these attributes which default to an empty string or list unless stated otherwise:

- `base` (required or use inheritance): a string of space-separated characters or combinations of characters and combining marks that are required to represent the language in common texts.
- `auxiliary` (optional): a string of space-separated characters or combinations of characters and combining marks that are not essential for the language support, but occur frequently in literature or names.
- `marks` (optional): combining marks needed for the glyph composition of `base` or `auxiliary` as well as any additional combining marks required for this orthography. Saving with `hyperglot-save` will also automatically add any marks that can be decomposed from characters in `base` or `auxiliary` to the `marks`. Marks that are not part of any characters should be added here and they will be required for fonts checking such languages.
- `punctuation` (optional): required punctuation.
- `numerals` (optional): numerals required. Do not include mathematical operators.
- `currency` (optional): recommended (rather than required) currency symbols.
- `autonym` (optional): the name of the language in the language itself using this orthography. If missing, the `autonym` defined in the parent language entry is used. It is expected that the `autonym` can be spelled with the orthography's `base`.
- `script` (required): English name of the main script used by the orthography, e.g. Latin, Arabic, Armenian, Cyrillic, Greek, Hebrew. When a language uses a combination of several scripts in conjunction each script forms its own orthography. It should follow ISO 15924.
- `status` (required, defaults to `primary`): one of the following (there can multiple orthographies with the same status per language):
  - `primary`: the current default orthography of a language,
  - `secondary`: a current but less frequently used orthography of a language (e.g. competing orthography gaining or losing popularity, orthography specific to a georgraphic location),
  - `historical`: an orthography that is no longer in use (all orthographies for a historical language ought to be historical),
  - `transliteration` a representation of a language using an alternative script.
  Orthographies with `secondary` status are ignored during language support detection, but used when detecting `orthography` support.
- `preferred_as_group` (optional, defaults to `false`) will combine all orthographies of this language. When used, a language is detected as supported only if all its orthographies with this attribute are supported. This is used for Serbian to require both Cyrillic-script and Latin-script orthographies to be supported and for Japanese to require Hiragana, Katakana, and Kanji orthographies to be supported.
- `note` (optional): a note of any kind.
- `design_requirements` (optional): a list of notes with general design considerations specific to this orthography. Ideally, phrased in a way that is font-format agnostic. A hint really.
- `design_alternates` (optional): a string of space separates characters from either `base`, `auxiliary` or `marks` which may require special treatment in font designs of those unicode points or combinations

### Criteria for establishing orthographies

Hyperglot serves primarily as a tool for language-support discovery. This is in contrast to other tools that attempt to set standards for assessment of quality in fonts or provide examples of characters from given language. Thus, Hyperglot’s main objective is to minimize false negatives, i.e. the number of languages falsely rejected during analysis of a font. This is the motivation behind the key *principle of minimality* applied to orthographies. Simply put, include only what needs to be included, nothing else.

1. Use at least two definitive authoritative sources to establish `base` character set. This set includes the minimal essential requirements needed to represent the language in writing which  typically maps to a standard alphabet or syllabary for the language or an approximation of thereof. Note that *ideally* these characters should be in a logical order used in the sources.
2. Characters that appear in frequent loan words or personal names should be included in `auxiliary`
3. Deprecated characters can be also included in `auxiliary`, e.g. `ş ţ` for Romanian. You may also consider setting up a secondary/historical orthography instead.
4. Contributors may decide to include digraphs or trigraphs for the sake of completeness, e.g. `ch` for Czech. All variations of uppercase and lowercase in common use should be included, e.g. `CH, Ch, ch`. These are not used during language-support analysis.
5. Make sure to include any required or auxiliary marks that are not already in `base` or `auxiliary` in `marks, e.g. the acute accent in Bulgarian Cyrillic.
6. Common punctuation characters used in literature should be included in `punctuation`. Analogically for `numerals`.
7. Currencies used in the countries where the language is considered official can be included as a recommendation in `currency`.

After the initial unbridled growth, we aim to focus at improving the authoritativeness of the data by better tracking its provenance.

Authoritative sources include, in the order of preference:

1. national/governmental standards,
2. official institutions,
3. educational materials, e.g. dictionaries,
4. literature of well-informed writers,
5. major religious works.

If possible, choose the primary sources over secondary sources such as Wikipedia or Omniglot. All sources used to compile the language and orthographic data should be listed in `sources`. Please, use the [APA style](https://apastyle.apa.org) and Markdown to add formatting (asterisks for italics, no need to format the links). Note that APA provides guidance regarding [references to religious works](https://apastyle.apa.org/style-grammar-guidelines/references/examples/religious-work-references), [missing reference information](https://apastyle.apa.org/style-grammar-guidelines/references/missing-information), or [referencing Wikipedia](https://apastyle.apa.org/style-grammar-guidelines/references/examples/wikipedia-references). Where available, provide a link or DOI. When citing an online source, try to find a permanent link (Wikipedia has those) to refer to a particular version of the document.

An example:

```yaml
sources:
- Breton language. (2024, August 21). In *Wikipedia*. https://en.wikipedia.org/wiki/Breton_language?oldid=1241510288
- '*The Unicode Common Locale Data Repository (CLDR)*. (2024, September 27). The Unicode Consortium. https://cldr.unicode.org'
- Alvestrand, Harald Tveit. (1995) *Characters and character sets for various languages.* Retrieved on September 6, 2021 from https://www.alvestrand.no/ietf/lang-chars.txt
```

Unless stated otherwise, the speaker counts are from Wikipedia.

#### Contribution notes

- Languages that are not written should not be included. Obviously.
- Languages that have some speakers should not be marked as `extinct` even if ISO standard says so.
- Languages needs to have an ISO code, and more generally speaking, should have active speakers (unless `extinct`) and not be purely scientific or theoretic in nature
- When adding or editing language data use the CLI commands `hyperglot-validate` to check your new data is compatible and use `hyperglot-save` to actually "save" the database in a standardized way (clean up, sorting, etc).
- Note a few things that will happen automatically when saving with `hyperglot-save`:
  - Marks found in `base` or `auxiliary` will get added to `marks`
  - All `marks` entries will be placed on top of `◌` for easier readability
  - All character list entries will be spaced with a single space between them, on one line
  - All language and orthography attributes will be sorted a-z; while this might not be the most intuitive, this ensures that data is always sorted the same, and thus comparing different versions of the data (with version control) yields predictable results
- When contributing code make sure to install the `pytest` package and run `pytest tests` to make sure no errors are detected. Ideally, write tests for any code additions or changes you have added.
- Add yourself to any language files you edit, and add your self to CONTRIBUTORS.txt
- Hyperglot uses a cache file `.hyperglot-cache` stored in a local directory. This may bite you as it currently only gets deleted when `hyperglot-save` is run. We hope to improve this in the future.

#### Inheritance

These attributes of an orthography can inherit from other languages/orthographies: `base`, `auxiliary`, `marks`, `punctuation`, `numerals`, `currency`, `design_requirements`, `design_alternates`.

Inheritance uses the iso code of the language to inherit from, with optional script, orthography status and source attribute.

Examples:

```yaml
# Inherit the base characters of eng to this orthography's base attribute
base: <eng>

# Inherit the auxiliary characters of eng, but into the base attribute of this orthography
base: <eng auxiliary>

# Inherit the ott transliteration orthography
base: <ott transliteration>

# Inherit the Cyrillic script base from srp (note script names are title case)
base: <srp Cyrillic>

# The inherited characters are inserted in place of the <...> so
base: Å <eng> À Á
# will result in:
base: Å A B C (etc. all from eng) À Á
```

**Warning:** Avoid `<g>` (less/greater) character highlights elsewhere in notes etc., e.g. use `‘g’` or `‹g›` (single guillemets) instead.

#### Using defaults

Since many languages of a given script will share some basic set of attributes there are convenience
defaults. When possible, use these defaults and avoid deeply nested inheritance chains.
You can use the [lib/hyperglot/extra_data/default.yaml] contents for inheritance, as if it were an ISO code, e.g.:

```yaml
numerals: <default Arabic>
punctuation: <default Latin> <default Cyrillic>
```

If you wish to expand the defaults file, talk to the maintainers (it only makes sense to include them for scripts with multiple languages).

#### Macrolanguages

[Macrolanguages](https://en.wikipedia.org/wiki/ISO_639_macrolanguage) are used in the ISO 639-3 standard to keep it compatible with ISO 639-2 in situations where one language entry in ISO 639-2 corresponds to a group of languages in ISO 639-3. Macrolanguages are typically not used by the Hyperglot’s main database. They are stored in a separate file in `other/hyperglot_macrolanguages.yaml` for convenience. However, in some situations, it is our preference to include some of the macrolanguages as if they were regular ISO 639-3 languages. This is done to simplify the listings or to deal with scarcity of information for its sub-languages. Besides the same attributes as language entries, macrolanguages can use the following:

- `includes` (required) contains a list of ISO 639-3 codes referring to sub-languages of the macrolanguage.
- `preferred_as_individual` (optional, defaults to `false`): set to `true` signifies that the macrolanguage us included in the main database as if it was a regular language.

### Example of an individual language with a single orthographic entry

`lib/hyperglot/data/dan.yaml`:

```yaml
orthographies:
 - base: a b c d e f g h i j k l m n o p q r s t u v w x y z å æ ø
   auxiliary: ǻ  # this character is used only in linguistic literature for Danish
   autonym: Dansk
   script: Latin
 name: Danish
 speakers: 6000000
 sources:
 - Ager, S. (2021, May 4). *Omniglot* https://www.omniglot.com
- Danish language. (2024, August 19). In *Wikipedia*. https://en.wikipedia.org/wiki/Danish_language?oldid=1241084738
- '*The Unicode Common Locale Data Repository (CLDR)*. (2024, September 27). The Unicode Consortium. https://cldr.unicode.org'
- Quotation mark. (2024, September 26). In *Wikipedia*. https://en.wikipedia.org/w/index.php?title=Quotation_mark&oldid=1247790780
 todo_status: strong  # status of the database record
```

### Example of a macrolanguage entry

`lib/hyperglot/data/fas.yaml`:

```yaml
name: Persian
includes: [pes, prs, tgk, aiq, bhh, haz, jpr, phv, deh, jdt, ttt]
speakers: 70000000
sources:
- Iranian Persian. (2024, July 31). In *Wikipedia*. https://en.wikipedia.org/wiki/Iranian_Persian?oldid=1237740929
- Ager, S. (2021, May 4). *Omniglot* https://www.omniglot.com
```

## Development and contributions

Contributions are most welcome. If you wish to update the database, submit a pull request with an editted and validated version of the `hyperglot/data` files. **Ideally**, use `hyperglot-validate` and `hyperglot-save`, as this will check and format the data in a way best suited to the database.

To start a new language entry you can use this template and include it in `hyperglot/data/xxx.yaml` as a new language draft in your pull request or github issue:

```yaml
name: # required
orthographies:
- autonym: # optional, name of the language in this language and orthography
  auxiliary: # optional
  base: # required
  currency: # optional
  marks: # optional
  numerals: <default>
  punctuation: <default>
  script: # required
  status: primary
sources: # required (a list)
# - an APA-style reference to the source of the data
speakers: # optional, integer
speakers_date: # optional, YYYY
note: # optional
design_requirements: # optional (a list)
# - optional
design_alternates: # optional (a list)
# - optional
status: living
validity: draft
contributors:
- Your Name # if you are contributing the data solely based on the sources
reviewers:
# - Your Name # if you claim expertise in this language
```

### Development

To run the script during development without having to constantly reinstall the pip package, you can use:

```shell
git clone https://github.com/rosettatype/hyperglot.git && cd hyperglot
pip install --upgrade --user --editable .
pip install -r requirements-tests.txt
```

To test the codebases after making changes run the `pytest` test suite:

```shell
pytest
```

To validate, sort, and verify the data integrity of `hyperglot/data` and get report of any possible formatting errors run:

```shell
hyperglot-validate
```

To save `hyperglot/data` use (this will format, sort and prune the data read in from the individual yaml files):

```shell
hyperglot-save
```

Note that this will *read* and *write* the yaml file and may change the formatting of your file.

## Other databases included in this repo

The following are YAML files distilled from the original data stored in subfolders with corresponding names.

- `other/cldr.yaml` - data (indexed by 4-letter script tags and ISO 639-3 language codes) from Unicode’s CLDR database.
- `other/iso-639-3.yaml` – data from IS0 639-3 (three-letter codes) with corresponding ISO 639-2 (older three-letter codes) and ISO 639-1 (two-letter codes) where available. Also includes language names and attributes from ISO 639-3.
- `other/iso-639-3_retirements.yaml` – language codes no longer available in ISO 639-3
- `other/iso-639-2_collections.yaml` – language collections from ISO 639-2 (no longer available in ISO 639-3)
- `other/opentype-language-tags.yaml` – OpenType language tags and names with their corresponding ISO 639-3 language codes
