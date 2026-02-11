# Common pitfalls (FAQ)

## Why doesn’t Serbian appear in the list of Latin-script languages?

Serbian is written in both, the Latin and Cyrillic scripts. Thus, Hyperglot requires support for both required orthographies. The same applies to Japanese, Ainu, Okinawan, Pontic Greek, Tlingit, and Xavánte.

## Why doesn’t Japanese appear in the list of Latin-script languages, even though it can be written using the Latin script?

Japanese written in the Latin script (rōmaji) is classified as a secondary orthography. Adjust the filter accordingly (for example, `--orthography=primary,secondary`) to include it.

## Why is German not showing up in the list of supported languages even though my font supports it?

Make sure to consider precomposed character combinations (using `--decomposed` and `--marks`) and the orthography you want to check. This guidance applies to any language, not just German.

## My font includes Katakana. Why is Japanese not listed as a supported language?

Hyperglot requires a font to include Hiragana, Katakana, and Kanji in order to consider Japanese fully supported.

## My font includes Balinese script characters. Why is Balinese not listed as a supported language?

The primary orthography for Balinese is actually Latin, as it is the most common way of writing the language today. To include checks for the secondary orthography that uses the Balinese script, set the flag to `--orthography=primary,secondary`.

## Why is language data for XYZ missing while YZX is included?

A language can be included if it meets two criteria:

1. It has an assigned [ISO 639-3 code](https://iso639-3.sil.org).
2. It has an established orthography that can be represented using [Unicode](https://unicode.org) characters.

If XYZ meets these requirements but is not yet in the database, please consider contributing or opening an issue](/issues).

The database uses ISO 639-3 language codes. If a language does not have an assigned ISO 639-3 code, we are currently unable to include it.

We recognize that opinions may differ on what constitutes a distinct language versus a dialect. However, to ensure consistency and interoperability, we adhere to the ISO 639-3 international standard.