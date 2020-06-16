# TODO

@Johannes

- [ ] review the README:
	- detection process
	- are all attributes listed
	- are all required attributes really required
	- do the defaults for the attributes correspond?
- [ ] I have removed all unnecessary macrolanguages and put them in a separate file. The only ones left are those that are included as individual. Hopefully it makes things simpler. I believe there should be no need for inheritance from a macrolanguage. Can you check this.
- [+] how should we handle combinations in {} for Central Yupik? Two characters with a combining mark over them. Aha!!
	- The combing double inverted breve U+0361 is just any other mark. For "u͡g" the normalization will decompose to u, g, combining mark, which is what we want.
- [ ] run analysis of characters in UDHR and compare this to our records, provide an error log
- [ ] check script adheres to README re "Orthographies with `deprecated` and `secondary` status are included only for the sake of completeness and ignored during language support detection."
- [ ] review and refactor decomposition rules and flags based on input charset:
	- [ ] Confirm default behaviour of extracting bases and marks from all charset characters, check precomposed codepoints where they exists, bases and marks too
	- [ ] Disregard precomposed codepoints and require only extracted bases + marks
- [ ] Confirm CLI --support for "base/aux"
- [+] Implement CLI --validity so users can choose a level over the default
- [ ] Refactor `save` script to remove redundant combining marks which are already implicitly listed via base+mark combinations
- [+] Implement "hyperglot" rename to database file and module
- [+] set status based on ISO (extinct, historical, …)
- [+] for orthography, do not inherit autonym, but inherit `numerals` if they exist.
- [+] add support for `preferred_as_individual: true` (default is false)
- [+] simplify validation:
	- [+] do not report errors for `todo_status: todo`
	- [ ] simply ignore spaces in combinations and characters sets (no need to report, no?)
		- NOTE: I'd keep these, just to get better data sanitization
	- [+] no need to report missing macrolanguages
	- [+] not all included languages need to be in the data
		- NOTE: In the long run this makes it hard to distinguish if a macro language is not being displayed because it is not supported, or because the data is faulty (i.e. a referenced sub language does not exist). We can re-instate these checks later.
	- [+] (bonus) use auxiliary and combinations to check for autonym name

- [+] check if all macrolanguages have been covered, i.e. if all ISO 639-3 languages marked as macrolanguages have a non-empty `includes` field. List those that do not.
	- NOTE: Currently also cross-checking iso data against rosetta data and emitting a warning if the rosetta data is missing one of those macrolanguages altogether
- [+] check if all names are iso-639-3, print output. The update might need to be done manually not to overwrite our preferred names.
	- NOTE: The only two cases of difference were quotes: 'Ta’izzi-Adeni Arabic' (iso: 'Ta'izzi-Adeni Arabic') and 'Ga’anda' (iso:'Ga'anda')


Notes:

- name and autonym of an orthography override those of languages (probably not needed now)
- [+] if there is not any orthography for a language, check if there is a macrolanguage which includes this language with some orthography. If so, use that.
- [+] when checking for language support in a font, ignore entries with `todo_status: todo`, set aside those with `todo_status: weak`. 
- [+] Ignore orthographies with `status: historical` and provide switch to ignore languages with status `historical` or `constructed`, but include by default.

@David

- [+] added header with a made up version number to both YAML files
- [+] separated macrolanguages to a new file in `hyperglot_macrolanguages.yaml`
- [ ] how to handle combinations in {} for Central Yupik?
- [ ] double check combinations for Hebrew
- [ ] add vowel combinations to Russian, Church Slavic, Ukrainian, Montenegrin
- [ ] review auxiliary
- [ ] check Cyrillic orthographies against: https://en.wiktionary.org/wiki/Appendix:Cyrillic_script
- [ ] add Armenian
- [ ] when adding Devanagari, include individual Bihari, Dogri, and Konkani languages

Ask externists to check:
- [ ] Albanian
- [ ] Hebrew & Yiddish

## Other

- [ ] ask others to check non-done languages (Ukrainian, Russian, Albanian, Polish, Spanish, Italian, …)
- [ ] work on presentation
- [ ] consider including Extensis character sets
- [ ] consider including Speak Easy
- [ ] consider including Adobe spreadsheets
- [ ] punctuation used by a language
	- [ ] include punctuation in checking that an autonym can be spelled in its provided orthography
- [ ] list OpenType features needed to support a language with a brief note about what the feature should do.
