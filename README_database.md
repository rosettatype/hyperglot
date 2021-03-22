# Database and contributing

## Database

The database is stored in the YAML file `lib/Hyperglot/hyperglot.yaml`.

### Languages

The highest level entries in the database represent languages indexed using the ISO 639-3 code. Each language entry can have these attributes which default to empty string or list unless stated otherwise:

- `name` (required): the English name of the language. This is also based on ISO 639-3. 
- `preferred_name` (optional): an override of the ISO 639-3 name. This is useful when the ISO 639-3 name  is pejorative or racist. We also use this to simplify very long names and where we have a preference (e.g. Sami over Saami). This can be turned off when using the database via the CLI tool or module to adhere strictly to ISO 639-3.
- `autonym` (optional): the name of the language in the language itself.
- `orthographies` (optional): a list of orthographies for this language. See below.
- `speakers` (optional) is a number of L1 speakers obtained from Wikipedia. Note that this is a number of speakers, thus one needs to account for literacy rate in particular language. This can an integer or a range.
- `speakers_date` (optional) is the publication date of the reference used for the speakers count on Wikipedia.
- `status` (required, defaults to `living`) the status of the language, may be one of `historical, constructed, living`.
- `source` (optional) is a list of source names used to define the orthographies, e.g. Wikipedia, Omniglot, Alvestrand. See below for the complete list.
- `validity` (required, defaults to `todo`): one of the following:
  - `todo` for work in progress,
  - `draft` for entries that are complete but have not been checked against any sources, yet,
  - `preliminary` for entries that have been checked with at least two online sources,
  - `verified` for entries confirmed by a native speaker or a linguist.
- `note` (optional): a note of any kind.


### Orthographies

A language can refer to one or more orthographies. An orthography specifies the script and characters from this script used to represent the language. There can be multiple orthographies for the same language using the same or different scripts. Each entry can have these attributes which default to an empty string or list unless stated otherwise:

- `base` (required or use `inherit`): a string of space-separated characters or combinations of characters and combining marks that are required to represent the language in common texts. This typically maps to a standard alphabet or syllabary for the language or an approximation of thereof.
- `auxiliary` (optional): a string of space-separated characters or combinations of characters and combining marks that are not part of the standard alphabet, but appear in very common loan words or in reference literature. Deprecated characters can be included here too, e.g. `ş ţ` for Romanian.
- `autonym` (optional): the name of the language in the language itself using this orthography. If missing, the `autonym` defined in the parent language entry is used. It is expected that the `autonym` can be spelled with the orthography's `base`.
- `inherit` (required or use `base`): the code of a language to copy the `base` and `auxiliary` strings from. In case the language has multiple orthographies, the first one for the same script is used.
- `script` (required): English name of the main script used by the orthography, e.g. Latin, Arabic, Armenian, Cyrillic, Greek, Hebrew. When a language uses a combination of several scripts in conjunction each script forms its own orthography.
- `status` (required, defaults to `primary`): the status of the orthography, may be one of: `deprecated, secondary, local, primary`. The value `local` refers to an orthography which is used only in a specific region. Orthographies with `secondary` status are ignored during language support detection, but used when detecting `orthography` support. Orthographies with `deprecated` status are included only for the sake of completeness.
- `preferred_as_group` (optional, defaults to `false`) will combine all orthographies of this language. When used, a language is detected as supported only if all its orthographies with this attribute are supported. This is used for Serbian to require both Cyrillic-script and Latin-script orthographies to be supported and for Japanese to require Hiragana, Katakana, and Kanji orthographies to be supported.
- `note` (optional): a note of any kind. We will add a note about other support requirements we know, e.g. OpenType features.


### Macrolanguages

[Macrolanguages](https://en.wikipedia.org/wiki/ISO_639_macrolanguage) are used in the ISO 639-3 standard to keep it compatible with ISO 639-2 in situations where one language entry in ISO 639-2 corresponds to a group of languages in ISO 639-3. Macrolanguages are typically not used by the Hyperglot’s main database. They are stored in a separate file in `other/hyperglot_macrolanguages.yaml` for convenience. However, in some situations, it is our preference to include some of the macrolanguages as if they were regular ISO 639-3 languages. This is done to simplify the listings or to deal with scarcity of information for its sub-languages. Besides the same attributes as language entries, macrolanguages can use the following:

- `includes` (required) contains a list of ISO 639-3 codes referring to sub-languages of the macrolanguage.
- `preferred_as_individual` (optional, defaults to `false`): set to `true` signifies that the macrolanguage us included in the main database as if it was a regular language.

### Example of an individual language with a single orthographic entry

```yaml
dan:
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

```yaml
fas:
  name: Persian
  includes: [pes, prs, tgk, aiq, bhh, haz, jpr, phv, deh, jdt, ttt]
  speakers: 70000000
  source: [Wikipedia]
```


## Development and contributions

Contributions are more most welcome. If you wish to update the database, submit a pull request with an editted and validated version of the `hyperglot.yaml` file. Ideally, use `hyperglot-validate` and `hyperglot-save`, as this will check and format the data in a way best suited to the database.

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

To validate, sort, and verify the data integrity of `hyperglot.yaml` and get report of any possible formatting errors run:

```shell
hyperglot-validate
```

To save `hyperglot.yaml` sorted alphabetically and pruned by iso keys:

```shell
hyperglot-save
```

Note that this will _read_ and _write_ the yaml file.

### Contribution notes

- Languages that are not written should not be included. Obviously.
- Languages that have some speakers should not be marked as `extinct` even if ISO standard says so.
- When adding or editing language data use the CLI commands `hyperglot-validate` to check your new data is compatible and use `hyperglot-save` to actually "save" the database in a standardized way (clean up, sorting, etc).
- When contributing code make sure to install the `pytest` package and run `pytest` to make sure no errors are detected. Ideally, write tests for any code additions or changes you have added.

## Sources

The main sources we used to build the database are:

- Alvestrand, Harald Tveit. Characters and character sets for various languages. 1995.
- [Ethnologue](http://ethnologue.org)
- [ISO 639-3](http://iso639-3.sil.org)
- [Omniglot](http://omniglot.com)
- [Unicode CLDR](http://unicode.org)
- [Wikipedia](http://wikipedia.org)

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
