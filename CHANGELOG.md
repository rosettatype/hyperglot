# A changelog for the lib/hyperglot language database and CLI tool (dd.mm.yyyy)

## 0.8.0 (WIP)
- LICENSE: Relicensed under Apache License 2.0
- FIX: `Shaper.check_joining` refined to not be more lenient and not fail fonts with other than one-to-one positional substitutions or general sequence manipulating `ccmp` code
- FIX Using a `--status` that does not include 'living' no correctly omits these languages
- TWEAK: Better output with `-v`: Consequently log skipped languages and orthographies plus the skipping the reason
- FEATURE: Added `-t`/`--shaping-threshold` that allows fine-tuning conjunct check failures by accounting for conjunct frequency
- FEATURE: Added `--no-shaping` flag to disable shaping checks entirely (on by default)
- DATA: Modified multitudes of `design_requirements`, dropped `design_alternates`
- DATA: `jpn` Latin orthography marked as secondary
- DATA: Introduced `combinations` orthography attribute
- DATA: `hin` and `mai` include syllable `combinations` with frequencies distributions (1: most common, 0: least common)
- TWEAK: `design_requirments` can now be either a string, or a dict of `note` + `alternates` (detailing which characters are affected)
- TWEAK: Minor tweak to logging in `Orthography`
- TWEAK: `Checker._check_shaping` with better pre-check to skip mark attachment checks for glyphs not in the font (obvious)
- TWEAK: Cleaned up multiple CLI options:
  - Added `--check` option to replace `--supportlevel`. `--check` takes any value of `base,auxiliary,punctuation,numerals,currency,all` or a comma-separated list of those
  - Removed `--include-historical` and `--include-historical` in favor or `--status` which accepts any combination of `LanguageStatus` or "all", defaults to "living"
  - Removed `--include-all-orthographies` in favor of `--orthography` which accepts any combination of `OrthographyStatus` or "all", defaults to "primary"
- TWEAK: Better logging output and logging strategies in the CLI/modules, `-v` provides basic language in/out and config logs, `-vv` gives very detailed support logs
- Removed the deprecated `STATUSES`, `ORTHOGRAPHY_STATUSES` and `SUPPORTLEVELS` from the codebase

## 0.7.3 (13.10.2025)
- DATA: Fixed to `cbi` (thanks @moyogo)
- TWEAK: Fixed `hyperglot-export` command for dumping expanded database

## 0.7.2 (15.01.2025)
- DATA: Minor refinements to `fin`, `ces` and `nav`
- DATA: Design requirements updated for `bos` and `srb` as well as some Cyrillic breve mentiones
- TWEAK: Improved inherited type where the original value is a yaml list
- TWEAK: Added parameter to instantiate a `Language` and force a reload of the data / ignoring the `.hyperglot-cache`

## 0.7.1 (07.10.2024)
- FIX: Fixed `hyperglot-data` error

## 0.7.0 (07.10.2024)
- DATA: All language yaml documents now have their `contributors` listed, some have `reviewers` listed
- DATA: **Massive* improvement of language `sources` with proper source citations where possible
- DATA: Added `punctuation`, `numerals` and `currency` attributes to orthographies - checking for these attributes will be added in the next update!
- DATA: Added `lib/hyperglot/extra_data/default.yaml` to include inheritable defaults per script
- DATA: Refined `jpn`, `ryu` and `ain` Katakana orthographies
- FEATURE: Orthography attributes can inherit from other languages with `<iso>` syntax, see [README](README_database.md)
- TWEAK: Improved loading time for repeat access by saving parsed language data cache file
- TWEAK: Orthographies can no longer have an `inherit` attribute
- TWEAK: Improved loading speed for repeat queries and indivudal language queries
- TWEAK: Refactored `Languages`, `Language` and `Orthography` object instantiation to always return parsed and defaulted nested objects
- TWEAK: Removed the `--speakers` and `--autonym` CLI options
- TWEAK: Removed the `--comparison` CLI option (see `examples` instead)
- TWEAK: Removed the `--languages` CLI option, use `hyperglot-info LanguageName/ISO` instead
- TWEAK: Removed the `--strict_iso` CLI option; use the python library to access this option, particularly `Language.get_name(script, strict_iso=True)`

## 0.6.4 (20.06.2024)
- FIX: Fixed an issue where trying to log missing shaping glyphs would crash in `FontChecker`
- FIX: Improved mark shaping detection to interpret ccmp substitutions of base + mark as correctly shaping (thanks @arialcrime)
- TWEAK: Cleaned up `hyperglot.language.Language` class and added attribute properties for dict properties with computed defaults (as opposed to writing defaults for missing attributes) as well as more code annotation
- TWEAK: `hyperglot.orthography.Orthography` object has `script_iso` attribute returning the mapped ISO 15924 script tag
- DATA: Added `lib/extra_data/script-names.yaml` with a list of all current Hyperglot scripts and a mapping to their ISO 15924 code equivalent
- DATA: Added di/tri-graphs to Czech and Hungarian orthographies and fixed their order
- DATA: Added Squamish (`squ`) (thanks @justinpenner)
- DATA: Unified "Geʽez" script with reversed comma, as opposed to previous mixed use of "Ge'ez/Fidel" and "Ge'ez"
- DATA: Amended spelling "Tai Viet" script in title case to match other script names
- DATA: Corrected spelling of "Bamum" script and language (instead of less used "Bamun" used in Hyperglot)
- DATA: Use "Coptic" instead of "Coptic/Numbian" script name
- DATA: Use "Burmese" script for language "Mon"
- DATA: Use "Baybayin" script name instead of "Tagalog (Baybayin, Alibata)"
- DATA: Fixed Toki Pona (`tok`) file name
- TWEAK: Make sure `Orthography.base_chars` and `Orthography.aux_chars` return no duplicates for decomposed character sequences
- TWEAK: Define `Languages`, `Language` and `Orthography` as module top level exports for easier importing, e.g. now: `from hyperglot import Language`

## 0.6.3 (08.04.2024)
- FIX: Set correct default values for `Language.status` and `Orthography.preferred_as_group` and provide validation and tests for these.
- TWEAK: Deprecated plain list `SUPPORTLEVELS, VALIDITYLEVELS, STATUSES, ORTHOGRAPHY_STATUSES` and replaced them with `SupportLevel, LanguageValidity, LanguageStatus, OrthographyStatus` enums throughout the code base. The deprecated values will be removed in the next minor version.
- TESTS: Added simple tox config for running test on all supported minor python versions

## 0.6.2 (22.3.2024)
- FIX: Fixed type hinting issue causing failure on python 3.8.x
- DATA: Added Banjar (`bjn`) (thanks @mahalisyarifuddin)
- DATA: Expanded Xavánte (`xav`) data (thanks @moyogo)

## 0.6.1 (30.1.2024)
- DATA: Refined Romanian by adding `design_alternates` explicitly

## 0.6.0 (16.01.2024)
- DATA: Refined Klingon (`tlh`) orthography and added a draft version of Toki Pona (`tok`)
- FEATURE: Implemented shaping checks for mark positioning when required by unencoded base + mark combinations or  `--decompose`
- FEATURE: Implemented shaping checks for connecting scripts to detect presence of required positional forms
- FEATURE: Implemented `hyperglot-report` command with same options as `hyperglot` and additional `--report-missing n`, `--report-marks n` and `--report-joining n` — or `--report-all n` to toggle all aforementioned — parameters/flags for outputting languages _almost_ supported by the font 
- TWEAK: Support checking is now done via `hyperglot.checker` objects for cleaner separation between language data and checking fonts
- TWEAK: Various python APIs and objects changed and refactored
- TWEAK: Bumped required python version to 3.8.0

## 0.5.3 (13.12.2023)
- DATA : Added Tlingit `tli` language data (thanks @jcrippen)
- DATA: Fixed inconsistent note about `Ŋ` in various languages (thanks @moyogo)
- TWEAK: Improved `hyperglot-validate` to spot lookalike characters in the wrong script, e.g. `a` (Latin U+0061) vs `а` (Cyrillic U+0430)
- TWEAK: Explicitly ignore non-yaml files (e.g. operating system or other) in the data when parsing
- TWEAK: Improved `hyperglot-validate` command to better catch yaml issues (thanks for reporting @jcrippen)

## 0.5.2 (23.11.2023)
- DATA: Removed orthography status `deprecated` and using `historical` for those instances
- DATA: Added Ethiopic languages `awn`, `byn`, `gez`, `har`, `sgw`, `tig`, `xan` and updated `tir` (thanks @dyacob and @NeilSureshPatel)
- DATA: Added Avestan
- DATA: Corrections to `jbo` (thanks @berrymot)
- DATA: Updated `sco` primary orthography (thanks @moyogo)
- DATA: Some fixes to `kkj` orthography (thanks @moyogo)
- DATA: Small note added to `Dagbani` (thanks @clauseggers and @moyogo)
- DATA: Fix to Shan (`shn`) containing some stray Latin characters
- FIX: Fix issue with file name conflicts on Windows systems

## 0.5.1 (21.06.2023)
- FIX: Fix pypi missing data files

## 0.5.0 (21.06.2023)
- FEATURE: Added `-l/--language` flag to show supported/not supported glyphs of a font for specific languages
- DATA: Restructured `hyperglot.yaml` into individual files for each language in `hyperglot/data/xxx/xxx.yaml`
- DATA: Fix two auxiliary glyphs in Georgian which where swapped uppercase / lowercase by mistake
- DATA: Small charset fixes to Kom `bkm` and Southern Samo `sbd` (thanks @moyogo)
- DATA: Small tweak to Afrikaans `afr` (thanks @iandoug)

## 0.4.5 (28.3.2023)
- DATA: Added languages and scripts for: Ainu, Akkadian, Ancient Egyptian, Mycenaean Greek, Linear A, Linear B, Minoan, Pontic Greek, Okinawan, Sumerian, Klingon, Minaen, Hadramautic, Qatabanian and Sabaean (big thanks to @gusbemacbe !)
- DATA: Added Kayah autonym
- DATA: Added design requirement note for `Ŋ`
- DATA: Improved Georgian, added Mtavruli and auxiliary
- DATA: Added historical orthographies for German and English that use `ſ`

## 0.4.4 (10.12.2022)
- FIX: Fixed orthography of Thai to not require `◌̍ ◌̎` in base checks

## 0.4.3 (10.12.2022)
- FIX: Fixed missing script attribute in 'lee' orthography
- FIX: Fixed typo in 'Oriya' script name

## 0.4.2 (25.11.2022)
- FEATURE: Implemented `hyperglot-data` CLI command to search and display language information returned by Hyperglot
- FEATURE: Implemented more convenient language access via attributes on hyperglot.languages.Languages, e.g. Languages().eng to access a hyperglot.language.Language object for "eng"
- DATA: Fix in Standard Malay encoding of `'` (thanks M. Mahali Syarifuddin and Caleb Maclennan)
- DATA: Added *numerous* Burkina Faso and other African languages (another huge thanks to @moyogo !)
- DATA: Added Oriya
- DATA: Added Kartvelian languages (kat, sva, xmf, lzz) (thanks Ana)

## 0.4.1 (18.08.2022)
- DATA: Dozens of African and North-American languages added and refined (thanks @moyogo !)
- DATA: Refined English `auxiliary`

## 0.4.0 (29.06.2022)
- DATA: Fix for Pinyin
- CLI: Introduced `--sort` (`alphabetic`, default, or `speakers`) and `--sort-dir` (`asc`, default, or `desc`)

## 0.3.9 (21.06.2022)
- DATA: Fix for Skolt Sami (soft sign)
- DATA: Fix for Hawaiian (okina)
- DATA: Fix for Thai including several missing marks and letters
- DATA: Fix in Buginese
- DATA: Updates to Indonesian and Standard Malay

## 0.3.8 (01.03.2022)
- DATA: Fix for Turkish orthography

## 0.3.7 (04.01.2022)
- DATA: Fix for Afrikaans orthography
- DATA: Corrected ISO code for Gen language

## 0.3.6 (11.11.2021)
- DATA: Added Benin languages
- DATA: Small fix to Portuguese

## 0.3.5 (07.09.2021)
- DATA: Revised Tamil orthography
- DATA: Added Apinayé, Karo and Awetí languages

## 0.3.4 (06.09.2021)
- FIX: Fixed an encoding issue affecting Windows environments
- DATA: Fixed typos in Buginese
- DATA: Reviewed Minangkabau orthography

## 0.3.3 (23.04.2021)
- DATA: Added Batak languages and refined Balinese
- FIX: Further improvement to detection of orthographies with unencoded base + mark combinations
- TWEAK: Refined the returned properties of `hyperglot.language.Orthography` to include base and auxiliary lists of _encoded_ characters as well as _required_ marks for
- TOOLS: Added scraper for fetching a mapping of Opentype language systems to ISO codes and saving them in `other/languagesystems.yaml`

## 0.3.2 (13.04.2021)
- DATA: Renamed `design_note` to `design_requirements` and made its data structure a list
- DATA: Introduced `design_alternates` - a list of characters which may require special design in a font supporting an orthography
- DATA: Added `design_alternates` for several Cyrillic and Latin languages

## 0.3.1 (12.04.2021)
- DATA: Corrected speaker count for Manipuri
- DATA: Updates to Andaandi and Old Nubian
- DATA: Minor formatting and duplicate fixes
- FIX: Fixed parsing issue that led for some languages to require marks in their support _as if_ the `--marks` flag was used
- TWEAK: `hyperglot.language.Language` no longer prunes or parses any character lists, but this is instead done on running the support checks by instantiating a `Orthography` object and using it for checking, leaving the dict representation of the yaml data in the `Language` untouched
- FEATURE: Introduced `hyperglot.language.Orthography` abstraction for easier access of parse lists vs yaml raw character strings
- TESTS: More refactored Languages, Language and new Orthography tests

## 0.3.0 (09.04.2021)
- DATA: Changed the way `marks` and decomposition are handled in the data entry and saving
- DATA: `base` and `auxiliary` may now contain unencoded base + mark character combinations without those getting decomposed on saving
- DATA: Updated approximately 50-100 languages which previously had unencoded base + mark combinations not saved in their character sets, since those were not unicode characters - this update added and retains those unencoded combinations for more comprehensive listing of the orthographies
- DATA: Marks are now always placed on `◌` in the data for easier readability
- CLI: Default checking (without `-m`) no longer requires implicit combining marks, meaning those which are retrieved from decomposing the characters - the default check will still require those marks, which are explicitly listed in `marks` and are not the result of decomposing the characters
- CLI: Introduced `-m/--marks` as a flag to require all marks for a support level check
- CLI: Changed `-m/--mode` to `-c/--comparison`
- TWEAK: Removed `hyperglot.parse.prune_superflous_marks` as no longer needed
- TWEAK: Introduced `hyperglot.parse.parse_marks`
- TWEAK: Removed `prune` and `pruneRetainDecomposed` flags from `Languages()` and changed default call to `Languages()` to no longer prune or parse its dict contents
- TWEAK: Only calls to `Language()` now parse the orthography data (with default `True` for argument `parse`)
- TWEAK: Renamed methods `hyperglot.languages.get_support_from_chars` to `supported` and `hyperglot.languages.has_support` to `supported`
- TWEAK: Added warnings and validation checks for multiple inheritance levels (e.g. A inherits from B inherits from C should instead be A inherits from C)

## 0.2.12 (06.04.2021)
- Data: Updated Ter Sami orthography as inheriting from Kildin Sami
- Data: Fixes to Kildin Sami
- Data: Some fixes to Marshallese
- Data: Added Ottoman Turkish and a transliteration orthography for it
- Data: Added Hanunoo
- Data: Replaced Single right comma (and other variants) with Modifier letter apostrophe for some Sami languages
- Data: 
- FIX: Fixed issue that caused to parse some fonts (#24)
- TWEAK: Allow inheriting an orthography without explicitly having a script present in the orthography, this will inherit the primary script orthography of the parent

## 0.2.11 (29.03.2021)
- DATA: Updated language data for Nubian languages and Japanese
- DATA: Introduced `transliteration` orthography status (started in 0.2.10)

## 0.2.10 (26.03.2021)
- DATA: Updated language data for Minang (xrg), Tamil (tam), Cherokee (chr), Tagalog (tgl), Aja (ajg), Khmer (khm), Madurese (mad), Javanese (jav) and others
- FIX: Reverted hotfix from 0.2.9 and implemented validation to use iso yaml file only for editable package installs and emit warning
- FIX: Refined `--decompose` and fixed an issue where the decompose option ended up returning more stringent matches than teh default
- FIX: `--output` output refactored to no longer expect the result to be structured by support levels
- TWEAK: Refactored multiple file input result intersection and union
- TESTS: Better tests relating to deomposed output
- TESTS: Added tests for multiple file input intersection and union results

## 0.2.9 (24.03.2021)
- HOTFIX: Prevent error message about missing file in CLI use

## 0.2.8 (24.03.2021)
- FIX: Fixed inheritence when it chains, e.g. Algerian Arabic inheriting from Tunisian Arabic which inherits from Standard Arabic
- FIX: Fixed inheritence missing `marks`, `design_notes` and `note`
- TWEAK: Make sure `marks` are saved in ordered form, so saving does not arbitrarily alter the order
- TESTS: Added tests for orthography inheritance
- DATA: Constrained speaker counts to integers only

## 0.2.7 (24.03.2021)
- DATA: Fixed various speaker counts containing malformed data
- DATA: More design notes for Latin-script languages
- DATA: Khmer added as draft, Armenian, Buginese, Georgian, Burmese, Lao and Thai refined
- TWEAK: Implemented validation for speaker count data

## 0.2.6 (23.03.2021)
- DATA: Various status updates, notes and reviewed orthographies
- DATA: Introduced `marks` attribute containing all combinging marks needed for an orthography
- FEATURE: Automatically extract and save `marks` from `base` data, plus retain any explicitly added `marks` in the data
- TWEAK: For default `hyperglot-save` calls automatically run validation to flag any remaining issues
- TWEAK: Flag legacy marks being used in charset data

## 0.2.5 (23.03.2021)
- DATA: Introduced `design_note` parameter
- DATA: Various language data updates and smaller fixes
- DATA: Several orthography fixes, thanks Denis Moyogo Jacquerye
- TWEAK: Changed orthography status names to `todo, draft, preliminary, verified`
- TWEAK: Improved `Language.get_orthography` to return better default picks and allow getting orthographies of specific script or status

## 0.2.4 (18.03.2021)
- First `pip` release :)

## 0.2.3 (10.03.2021)
- FEATURE: Implemented `--include-all-orthographies` to check all but `deprecated` orthographies and changed default behaviour to only list `primary` orthographies
- TWEAK: Implemented treating orthographies with `preferred_as_group` as one for checks
- TWEAK: Languages with multiple `primary` orthographies will match if one is supported
- TWEAK: `Languages` can be initiated with `pruneRetainDecomposed` to keep any precomposed characters from the database when using `prune` (which decomposes them to base + mark)
- TWEAK: Improved tests for CLI and improved and fixed some parsing tests
- FIX: Marginal cases fixed where using `parse_chars` and already parsed lists would merge a mark with a predeceding base glpyh and result in a erraneous list of base/aux characters
- DATA: Added uppercase to bicameral scripts
- DATA: All languages now have a `primary` orthography
- DATA: Introduced `preferred_as_group` orthography attribute
- TESTS: Config to ignore other library's warnings

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