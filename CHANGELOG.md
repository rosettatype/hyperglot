# A changelog for the lib/fontlang CLI tool

# 0.1.3 (23.01.2020)
- TWEAK: Merged `fontlang` with Rosetta Language DB repo
- TWEAK: Updated data structure in YAML and added `Language` class for convenience

# 0.1.2
- FEATURE: `-o` flag to specify an output yaml file path
- FEATURE: `-n` flag to display language names in native spelling (where available)
- FEATURE: `-u` flag to display language users (if available)
- TWEAK: Updated `rosetta.yaml` language database

# 0.1.1
- FEATURE: `-s` flag with "base" or "aux" values to set support level to check
- TWEAK: Support output sorted by scripts and language DB status (informs about not "done" langs being match)
- TWEAK: Added basic font validation for the passed in file path
- TWEAK: Fixed relative imports and cli usage for dev
- FIX: Language database typo fix

# 0.1.0
- FEATURE: MVP with basic `$ fontlang path/to/font` command