# Rosetta’s database of languages

A database of languages and standard characters required for their representation.

This project started with a seemingly simple question: when can one claim that a font *F* supports a language *L*. This is needed for several reasons:

1. to organize and serve fonts to customers
2. to better promote fonts with extensive langauge support
3. to build character sets (and glyph sets) before development
4. to test fonts, e.g. to heuristically create kerning pairs for consideration
5. and probably quite a few reasons unrelated to typeface design

A few notes to illustrate why the question of language support is complicated:

1. a single language can be written using different orthographies in one or more scripts
2. languages are not isolated, there are loan word, names etc. from other languages
3. what one person considers a dialect, is a language for someone else
4. different kinds of texts require differnt vocabulary and hence different characters

We have decided to take a pragmatic approach and reduce the problem to finding standard character set of each language (typically an official alphabet or syllabary or its approximation) and occassionally we provide a list of auxiliary characters used in reference literature (linguistics) or in very common loan words. In case the script used is bicameral, only lowercase versions of characters are provided with a few exceptions.

We are also providing a command-line tool to automate the analysis of language support

**This is a work in progress provided AS IS. If you want to contribute, do get in touch!**

## Structure of the Rosetta database

1. language records are indexed by ISO 639-3 three-letter codes
2. a language `name` is also based on ISO 639-3. There is an option to override this and set a `preferred_name` in case the ISO name is pejorative or racist. We also use this to simplify very long names and where we have a preference (e.g. Sami over Saami).
3. a language can contain a list of `orthographies`
4. in case a language is a macrolanguage, it has an attributed `includes` which is a list of language codes of the sub-languages. If a sub-language does not have any orthography defined, it can use one defined for the macrolanguage. If there is one.
5. an orthography is a list of character sets:
	- `base` is a string of space-separated characters from the language’s standard alphabet, syllabary, or an approximation of those.
	- `auxiliary` is a string of space-separated characters that are used in very common loan words or in reference literature (e.g. linguistic)
	- `combinations` is a string with combinations of characters or characters and marks that should be supported by the font.
6. each orthography has a `script` specified with a four-letter Unicode tag (Latn, Arab, Cyrl, …)
7. an `autonym` (name of the language in the language itself) is typically specified on the level of orthographies, but sometimes it is specified for a language, e.g. for a macrolanguage. The orthography autonym and name override the corresponding attributes of the language.
8. each languages can have the following additional attributs:
	- a number of native `speakers`. Note that this is a number of speakers, thus one needs to account for literacy rate in particular language. This can be a range.
	- a `status` which refers to a living language by default (when missing), or `historical`, or `constructed`.
	- `source` is a list of sources used to define the orthographies.

The database is stored in a YAML file `data/rosetta.yaml`. Here are two basic examples:

### An individual language with one orthography

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

### A macrolanguage

```
fas:
  name: Persian
  includes: [pes, prs, tgk, aiq, bhh, haz, jpr, phv, deh, jdt, ttt]
  speakers: 70000000
  source: [Wikipedia]
```

## The command-line tool

todo

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

- David Březina  
- Sergio Martins  
- Johannes Neumeier
- Toshi Omagari
