# TODO

@Johannes

- [ ] set status based on ISO (extinct, historical, …)
- [ ] for orthography, do not inherit autonym, but inherit `numerals` if they exist.
- [+] add support for `preferred_as_individual: true` (default is false)
- [ ] simplify validation:
	- do not report errors for `todo_status: todo`
	- simply ignore spaces in combinations and characters sets (no need to report, no?)
	- no need to report missing macrolanguages
	- not all included languages need to be in the data
	- (bonus) use auxiliary and combinations to check for autonym name

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

- [ ] add vowel combinations to Russian, Church Slavic, Ukrainian, Montenegrin

Ask to check:
- Albanian
- Hebrew & Yiddish

Later:

- [ ] review combinations (are all codepoints combining, …)
- [ ] review auxiliary
- [ ] check Cyrillic orthographies against: https://en.wiktionary.org/wiki/Appendix:Cyrillic_script

## Other

- [ ] ask others to check non-done languages (Ukrainian, Russian, Albanian, Polish, Spanish, Italian, …)
- [ ] work on presentation
- [ ] consider including Extensis character sets
- [ ] consider including Speak Easy
- [ ] consider including Adobe spreadsheets
- [ ] punctuation used by a language
	- [ ] include punctuation in checking that an autonym can be spelled in its provided orthography
- [ ] list OpenType features needed to support a language with a brief note about what the feature should do.

## Missing macrolanguages

- doi
- kok
- nep
- ori
