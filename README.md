# Rosetta’s database of languages

A database of languages and characters required for their representation. 

Partially based on Unicode CLDR, Underware’s Latin Plus and other sources.

**A work in progress!**


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
  speakers: number of native/L1 speakers
  source: a list of sources of the data for the base/auxiliary/combinations characters
  status: status of the language: historical, constructed, empty if living/contemporary
  note: a note :)
  todo_status: status regarding the completeness of this entry: todo, weak, strong, done
  ```
