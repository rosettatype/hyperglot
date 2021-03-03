# A changelog for the lib/hyperglot CLI tool

## 0.2.3 (WIP)
- TWEAK: Improved tests for CLI and improved and fixed some parsing tests
- DATA: Added uppercase to bicameral scripts
- DATA: All languages now have a `primary` orthography

## 0.2.2 (02.03.2021)
- TWEAK: `Languages()` now takes a `validity` argument to filter by validity ('weak' or better by default)
- TWEAK: `parse_chars` now will put decomposition components on in the input list to the end of the list
- TWEAK: Languages require an orthography that has status `primary`

## 0.2.1 (03.02.2021)
- DATA: Updated and added many scripts and languages and their speaker counts

## 0.2.0 (28.01.2021)
- FEATURE: Added `--decomposed` flag that determines if a font is required to have all glyphs of a language as code points, or if supporting all combining marks is sufficient
- TWEAK: Renamed module and database to `hyperglot`
- TWEAK: `--strict-support` refactored to `--validity` with default `weak` to pick the level of required validity on the languages that should get matched
- TWEAK: Saving and validating enforces removal of superflous mark characters that are getting implicitly extracted via glyph decomposition
- TWEAK: Detection automatically extracts all required mark glyphs for languages and the database has been pruned of any no longer required mark glyphs listed. Using the `hyperglot-save` will apply this pruning and save the database in its cleaned up state
- TESTS: Added tests for the Language and Languages class
- TESTS: Added test for the CLI options running against actual font files
- DOCS: Overhauled and updated the README to all latest changes

## 0.1.14 (27.5.2020)
- FIX: Refined character parsing to also include the encoded form of any decomposable glyphs

## 0.1.13 (15.5.2020)
- FIX: Improved character set parsing from database properly decomposing any combining characters into their parts and checking against those
- TESTS: Added first pytest for above case

## 0.1.12 (14.5.2020)
- FEATURE: Added `--strict-support` flag (default False) to explicitly trigger warning about languages with unconfirmed status. Since those languages have well researched charset information but just have not been confirmed by several expert sources we still want to include them in the count. Using `--strict-support` excludes (but lists separately) all those languages which we have not been able to confirm
- TWEAK: Renamed `--strict` flag to `--strict-iso` to be more discriptive
- TWEAK: Database file linking, one more time... as per 0.1.10
- TWEAK: Added validation check to prevent non-space separators in character list data

## 0.1.11 (10.4.2020)
- FEATURE: Implemented `fontlang-export` CLI script to export the rosetta.yaml with expanded inherits to a file, usage: `$ fontlang-export thefile.yaml`

## 0.1.10 (17.3.2020)
- FIX: Refactored `setup.py` to include the databased file relative to the package

## 0.1.9 (19.2.2020)
- FIX: "Inverted" the `preferred_as_individual` outcome, e.g. those languages should suppress any included languages from being listed and be listed as one language instead

## 0.1.7 & 0.1.8 (18.02.2020)
- FIX: Made sure `preferred_as_individual` in fact also removes the language that is being inheritted from the matches
- TWEAK: Update `fontlang-save` and sorting to not include inheritted attributes
- TWEAK: Updated and fixed validation for `status` attributes

## 0.1.6 (07.02.2020)
- FEATURE: Implemented support for the `preferred_as_individual` attribute on macro languages
- FEATURE: Added `--strict` flag to display language names and macrolanguages as per ISO data
- TWEAK: Implemented orthography attribute `inherit` to inherit another language's orthography for that `script` (if one exists)
- FIX: Language names with countries in brackets no longer have their closing parenthesis cut off
- TWEAK: Updated `fontlang-validate` to spec

## 0.1.5 (30.01.2020)
- FIX: More robust relative file path loading for database file
- TWEAK: `-o` output is now of same structure for single file input, and indexed by file name for several file input
- TWEAK: `-o` filters the languages' orthographies to only supported ones
- TWEAK: Added validation check to confirm orthographies have a 'script'
- TWEAK: Refactored validation script to `fontlang-validate` CLI command
- TWEAK: Languages without orthographies that are included in macrolanguages that do have orthographies silently inherit the macrolanguage's orthographies
- FEATURE: Added `fontlang-save` CLI command to re-save the `rosetta.yaml` sorted alphabetically
- FEATURE: Added `--include-historical` and `--include-constructed` flags to include those languages in results
- FEATURE: Added `--version` and `--verbose` flags

## 0.1.4 (28.01.2020)
- FEATURE: Added `-m` option ('individual', 'union', 'intersection') to compute a support comparison of several passed in fonts
- TWEAK: You can now pass in any number of font paths. By default one after the other is analyzed
- TWEAK: Make sure to print `preferred_name` if available

## 0.1.3 (23.01.2020)
- TWEAK: Merged `fontlang` with Rosetta Language DB repo
- TWEAK: Updated data structure in YAML and added `Language` class for convenience

## 0.1.2
- FEATURE: `-o` flag to specify an output yaml file path
- FEATURE: `-n` flag to display language names in native spelling (where available)
- FEATURE: `-u` flag to display language users (if available)
- TWEAK: Updated `rosetta.yaml` language database

## 0.1.1
- FEATURE: `-s` flag with "base" or "aux" values to set support level to check
- TWEAK: Support output sorted by scripts and language DB status (informs about not "done" langs being match)
- TWEAK: Added basic font validation for the passed in file path
- TWEAK: Fixed relative imports and cli usage for dev
- FIX: Language database typo fix

## 0.1.0
- FEATURE: MVP with basic `$ fontlang path/to/font` command