# A changelog for the lib/fontlang CLI tool

## 0.1.6 (07.02.2020)
- FEATURE: Implemented support for the `preferred_as_individual` attribute on macro languages
- FEATURE: Added `--strict` flag to display language names and macrolanguages as per ISO data
- TWEAK: Implemented orthography attribute `inherit` to inherit another language's orthography for that `script` (if one exists)
- FIX: Language names with countries in brackets no longer have their closing parenthesis cut off

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