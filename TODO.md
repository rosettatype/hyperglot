# TODO

- [ ] consider including Extensis character sets
- [ ] consider including Speak Easy
- [ ] consider including Adobe spreadsheets

@Johannes

- [ ] double check if YAML is well formed, list-type fields are always lists etc.
- [ ] compare scraped speaker counts with those currently in the DB: this could lead to improved RE and migh help us update the existing counts in the DB. I would prefer to do this manually.
- [ ] add language names and speaker counts where missing or where -- is used
- [ ] add a date (year) for the speaker count information, to the field `speakers_date`.
- [ ] add langtool, refactor to work with the new format
- [ ] langtool should subset the rosetta.yaml per font
- [ ] check if all macrolanguages have been covered, i.e. if all ISO 639-3 languages marked as macrolanguages have a non-empty `includes` field. List those that do not.
- [ ] check if all names are iso-639-3, print output. The update might need to be done manually not to overwrite our preferred names.
- [ ] make sure characters used in autonyms are also in the base for corresponding orthography
- [ ] add licence to this repo

Notes:

- name and autonym of an orthography override those of languages (probably not needed now)
- if there is not any orthography for a language, check if there is a macrolanguage which includes this language with some orthography. If so, use that.
- when checking for language support in a font, ignore entries with `todo_status: todo`, set aside those with `todo_status: weak`. Ignore orthographies with `status: historical` and provide switch to ignore languages with status `historical` or `constructed`, but include by default.

@David

- [ ] double check Swahili macrolanguage
- [ ] srd -> macrolanguage, Sardinian
- [ ] orm-> macrolanguage, Oromo
- [ ] kur -> inclusive language, Kurdish
- [ ] aze -> inclusive language, Azerbaijani
- [ ] que -> macrolanguage, Quechua
- [ ] complete Arabic, Persian, and Malay sub-languages
