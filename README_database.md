# Database and contributing

## Database

The database is stored in the YAML file `lib/Hyperglot/data/xxx.yaml`.

### Languages

The highest level entries in the database represent languages indexed using the ISO 639-3 code. (We are aware that opinions regarding what constitutes a dialect or language differ, but we have to adhere to an international standard.) Each language entry can have these attributes which default to empty string or list unless stated otherwise:

- `name` (required): the English name of the language. This is also based on ISO 639-3. 
- `preferred_name` (optional): an override of the ISO 639-3 name. This is useful when the ISO 639-3 name  is pejorative or racist. We also use this to simplify very long names and where we have a preference (e.g. Sami over Saami). This can be turned off when using the database via the CLI tool or module to adhere strictly to ISO 639-3.
- `autonym` (optional): the name of the language in the language itself.
- `orthographies` (optional): a list of orthographies for this language. See below.
- `speakers` (optional) is a number of L1 speakers. Note that this is a number of speakers, not a number of readers. Only integer values are allowed. If a source lists a range the maximimum of the estimated range is listed.
- `speakers_date` (optional) is the publication date of the reference used for the speakers count on Wikipedia.
- `status` (required, defaults to `living`) the status of the language, may be one of `historical, constructed, living`.
- `source` (optional) is a list of source names used to define the orthographies, e.g. Wikipedia, Omniglot, Alvestrand. See below for the complete list.
- `validity` (required, defaults to `todo`): one of the following:
  - `todo` for work in progress,
  - `draft` for entries that are complete but have not been sufficiently verified, yet,
  - `preliminary` for entries that have been verified by at least two online sources,
  - `verified` for entries verified by a competent speaker or a linguist.
- `note` (optional): a note of any kind.


### Orthographies

A language can refer to one or more orthographies. An orthography specifies the script and characters from this script used to represent the language. There can be multiple orthographies for the same language using the same or different scripts. Each entry can have these attributes which default to an empty string or list unless stated otherwise:

- `base` (required or use `inherit`): a string of space-separated characters or combinations of characters and combining marks that are required to represent the language in common texts. This typically maps to a standard alphabet or syllabary for the language or an approximation of thereof. Note that _ideally_ these characters should be in logical order that adheres to the orthography.
- `auxiliary` (optional): a string of space-separated characters or combinations of characters and combining marks that are not part of the standard alphabet, but appear in very common loan words or in reference literature. Deprecated characters can be included here too, e.g. `ş ţ` for Romanian.
- `marks` (optional): combining marks needed for the glyph composition of `base` or `auxiliary` as well as any additional combining marks required for this orthography. Saving will also automatically add any marks that can be decomposed from characters in `base` or `auxiliary` to the `marks`. Also marks that are not part of any characters should be added here and they will be required for fonts checking such languages.
- `autonym` (optional): the name of the language in the language itself using this orthography. If missing, the `autonym` defined in the parent language entry is used. It is expected that the `autonym` can be spelled with the orthography's `base`.
- `script` (required): English name of the main script used by the orthography, e.g. Latin, Arabic, Armenian, Cyrillic, Greek, Hebrew. When a language uses a combination of several scripts in conjunction each script forms its own orthography. It should follow ISO 15924.
- `status` (required, defaults to `primary`): one of the following (there can multiple orthographies with the same status per language):
  - `primary` for the current, main orthography of a language,
  - `secondary` for a current, but less frequent, orthography (e.g. competing orthography gaining or losing popularity),
  - `local` for a secondary orthography limited to a small geographic region (specified in note),
  - `historical` for an orthography that is no longer in use (all orthographies for a historical language ought to be historical),
  - `transliteration` for an orthography used for transliterations (e.g. transliteration of Standard Arabic in the Latin script).
  Orthographies with `secondary` status are ignored during language support detection, but used when detecting `orthography` support.
- `preferred_as_group` (optional, defaults to `false`) will combine all orthographies of this language. When used, a language is detected as supported only if all its orthographies with this attribute are supported. This is used for Serbian to require both Cyrillic-script and Latin-script orthographies to be supported and for Japanese to require Hiragana, Katakana, and Kanji orthographies to be supported.
- `note` (optional): a note of any kind.
- `design_requirements` (optional): a list of notes with general design considerations specific to this orthography. Ideally, phrased in a way that is font-format agnostic. A hint really.
- `design_alternates` (optional): a string of space separates characters from either `base`, `auxiliary` or `marks` which may require special treatment in font designs of those unicode points or combinations

#### Inheritance

These attributes of an orthography can inherit from other languages/orthographies: `base`, `auxiliary`, `marks`, `punctuation`, `numerals`, `currency`, `design_requirements`, `design_alternates`.

Inheritance uses the iso code of the language to inherit from, with optional script, orthography status and source attribute.

Examples:

```
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

Note: Avoid `<g>` character highlights in notes etc., use `‘g’` or `/'/` instead.


### Macrolanguages

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
 source: [Omniglot, Wikipedia, CLDR]
 todo_status: strong  # status of the database record
```

### Example of a macrolanguage entry

`lib/hyperglot/data/fas.yaml`:

```yaml
name: Persian
includes: [pes, prs, tgk, aiq, bhh, haz, jpr, phv, deh, jdt, ttt]
speakers: 70000000
source: [Wikipedia]
```


## Development and contributions

Contributions are more most welcome. If you wish to update the database, submit a pull request with an editted and validated version of the `hyperglot/data` files. **Ideally**, use `hyperglot-validate` and `hyperglot-save`, as this will check and format the data in a way best suited to the database.

### Development

To run the script during development without having to constantly reinstall the pip package, you can use:

```shell
git clone https://github.com/rosettatype/hyperglot.git && cd hyperglot
pip install --upgrade --user --editable .
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

Note that this will _read_ and _write_ the yaml file.

### Contribution notes

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

## Sources

The main sources we used to build the database are:

- Alvestrand, Harald Tveit. Characters and character sets for various languages. 1995.
- [Ethnologue](http://ethnologue.org)
- [ISO 639-3](http://iso639-3.sil.org)
- [Omniglot](http://omniglot.com)
- [Unicode](http://unicode.org)
- [Wikipedia](http://wikipedia.org)
- Grierson, George Abraham. Linguistic survey of India. Delhi: Low Price Publications. 2012.

Further sources are listed for each language.

The autonyms were sourced from Ethnologue, Wikipedia, and Omniglot (in this order preferrably).
The speaker counts are from Wikipedia.

## Other databases included in this repo

The following are YAML files distilled from the original data stored in subfolders with corresponding names.

- `other/alvestrand.yaml` – data (indexed by ISO 639-3 codes) scraped from Alvestrand (see Sources below).
- `other/cldr.yaml` - data (indexed by 4-letter script tags and ISO 639-3 language codes) from Unicode’s CLDR database.
- `other/iso-639-3.yaml` – data from IS0 639-3 (three-letter codes) with corresponding ISO 639-2 (older three-letter codes) and ISO 639-1 (two-letter codes) where available. Also includes language names and attributes from ISO 639-3.
- `other/iso-639-3_retirements.yaml` – language codes no longer available in ISO 639-3
- `other/iso-639-2_collections.yaml` – language collections from ISO 639-2 (no longer available in ISO 639-3)
- `other/opentype-language-tags.yaml` – OpenType language tags and names with their corresponding ISO 639-3 language codes
