# Rosetta’s database of languages

A database of languages and standard characters required for their representation. Based on Unicode CLDR, Wikipedia, Omniglot, and Alvestrand (see below). If you want to contribute, get in touch.

**This is a work in progress provided AS IS.**

## Methodology

*todo*

## Structure of the Rosetta database

The database is stored in a YAML file `data/rosetta.yaml`. Each language entry can take the following form. Not all attributes are always present.

```
<ISO 639-3 code>:
  orthographies: a list of orthographies for the language
  - base: list of required characters, standard character set, standard alphabet
    auxiliary: list of auxiliary characters
    combinations: list of required combinations of characters and marks
    name: English name of the language in this orthography
    autonym: autonym of the language in this orthography
    script: script of this orthography
    status: status of the orthography: none, historical, …
    note: a note :)
  name: ISO 639-3 name of the language
  autonym: autonym of the language
  includes: a list of sub-languages in case this is a macrolanguage
  speakers: number of native (L1) speakers
  source: a list of sources of the data for the base/auxiliary/combinations characters
  status: status of the language: historical, constructed, empty if living/contemporary
  note: a note :)
  todo_status: status regarding the completeness of this entry: todo, weak, strong, done
```

## Other databases

The following are YAML files distilled from the original data stored in subfolders with corresponding names.

- `data/alvestrand.yaml` – data (indexed by ISO 639-3 codes) scraped from *Alvestrand, Harald Tveit. Characters and character sets for various languages. 1995.*
- `data/cldr.yaml` - data (indexed by 4-letter script tags and ISO 639-3 language codes) from Unicode’s CLDR database.
- `data/iso-639-3.yaml` – data from IS0 639-3 (three-letter codes) with corresponding ISO 639-2 (older three-letter codes) and ISO 639-1 (two-letter codes) where available. Also includes language names and attributes from ISO 639-3.
- `data/iso-639-3_retirements.yaml` – language codes no longer available in ISO 639-3
- `data/iso-639-2_collections.yaml` – language collections from ISO 639-2 (no longer available in ISO 639-3)
- `data/opentype-language-tags.yaml` –OpenType language tags and names with their corresponding ISO 639-3 language codes

The following data is not used or used only to build comparisons:

- `data/other/extensis` – character sets compiled by Extensis/WebINK
- `data/other/iana` – from [IANA language subtag registry](https://www.iana.org/assignments/lang-subtags-templates/lang-subtags-templates.xhtml)
- `data/other/latin-plus` - data from a [Latin-only database compiled by Underware](https://underware.nl/latin_plus/)

## Credits

David Březina  
Sergio Martins  
Johannes Neumeier
Toshi Omagari
