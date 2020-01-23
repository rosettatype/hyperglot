# TODO

@Johannes

- [ ] add langtool, refactor to work with the new format
- [ ] langtool should subset the rosetta.yaml per font
- [ ] double check if YAML is well formed, list-type fields are always lists etc.
- [ ] add language names and speaker counts where missing or where -- is used
- [ ] add a date (year) for the speaker count information, to the field `speakers_date`.
- [ ] compare scraped speaker counts with those currently in the DB: this could lead to improved regular expression and migh help us update the existing counts in the DB. I would prefer to do this manually.
- [ ] add a licence document to this repo

Notes:

- name and autonym of an orthography override those of languages (probably not needed now)
- if there is not any orthography for a language, check if there is a macrolanguage which includes this language with some orthography. If so, use that.
- when checking for language support in a font, ignore entries with `todo_status: todo`, set aside those with `todo_status: weak`. Ignore orthographies with `status: historical` and provide switch to ignore languages with status `historical` or `constructed`, but include by default.

@David

- [+] check if all macrolanguages have been covered, i.e. if all ISO 639-3 languages marked as macrolanguages have a non-empty `includes` field. List those that do not.
- [+] check if all names are iso-639-3, print output. The update might need to be done manually not to overwrite our preferred names.
- [+] make sure characters used in autonyms are also in the base for corresponding orthography
- [ ] review combinations (are all codepoints combining, …)
- [ ] review auxiliary
- [ ] check Cyrillic orthographies agains https://en.wiktionary.org/wiki/Appendix:Cyrillic_script
- [ ] double check Swahili macrolanguage
- [ ] convert these to macrolanguages:
	aze Azerbaijani
	kur Kurdish
	mon Mongolian
	bik Bikol
	est Estonian
	kln Kalenjin
	lav Latvian
	luy Luyia
	orm Oromo
	que Quechua
	sqi Albanian
	srd Sardinian
	zap Zapotec
- [ ] double check these autonyms:
	abk Abkhazian - Аҧсшәа‎
	ady Adyghe - Адыгабзэ‎
	agx Aghul - Агъул‎
	ani Andi - Мицци‎
	bak Bashkir - Башҡортса‎
	bhh Bukharic - Бухорӣ
	bhh Bukharic - בוכארי
	chu Church Slavic - Церковнослове́нскїй
	chv Chuvash - Чӑвашла‎
	crh Crimean Tatar - Qırımtatar tili
	dlg Dolgan - Дулҕан
	ems Pacific Gulf Yupik - Sugpiaq
	inh Ingush - Гӏалгӏай‎
	jdt Judeo-Tat - Juwri
	kaa Kara-Kalpak - Қарақалпақ тили‎
	kum Kumyk - Къумукъ‎
	kur Kurdish - Kurdî
	kur Kurdish - Kurdî
	lez Lezghian - Лезги‎
	mhr Eastern Mari - Олык Марий‎
	mrj Western Mari - Кырык Мары‎
	oaa Orok - Уйльта
	ron Romanian - Română
	rut Rutul - Мыхӏабишды‎
	sah Yakut - Сахалыы‎
	sgh Shughni - Хуг̌ну̊н зив
	sjd Kildin Sami - Кӣллт Са̄мь
	tat Tatar - Татарча‎
	tkr Tsakhur - Ts‘əxna miz
	tly Talysh - Толыши
	tly Talysh - Tolışi‎
	tyv Tuvinian - Тыва‎
	uzn Northern Uzbek - Ўзбекча
	uzn Northern Uzbek - O‘zbekcha
	uzs Southern Uzbek - اوزبیکی
	ydd Eastern Yiddish - ייִדיש
	yih Western Yiddish - ייִדיש
	aat Arvanitika Albanian - Αρβανίτικα
	bem Bemba (Zambia) - Chibemba
	cak Kaqchikel - Kaqchikel Chʼabʼäl
	cic Chickasaw - Chikashshanompa’
	cic Chickasaw - Chikashshanompa’
	con Cofán - A’ingae
	fao Faroese - Føroyskt
	gwi Gwichʼin - Dinju Zhuh K’yuu
	haa Han - Häł gołan
	haw Hawaiian - ’Olelo Hawai’i
	hop Hopi - Hopilàvayi
	kek Kekchí - Q’eqchi’
	mgo Meta' - Mɨta’
	moh Mohawk - Kanien’kéha
	mrq North Marquesan - ’Eo ’Enana
	mqm South Marquesan - ʻEo ʻEnata
	rar Rarotongan - Māori,
	ruo Istro Romanian - Rumârește
	sjk Kemi Sami - Samääškiela
	sia Akkala Sami - Bidumsámegiella
	sjt Ter Sami - Са̄мькӣлл
	srm Saramaccan - Saamáka
	tvl Tuvalu - Te ’gana Tūvalu
	twq Tasawaq - Ingalkoyyu’
	tzo Tzotzil - Bats’i k’op
	vie Vietnamese - Tiếng Việt
	wls Wallisian - Fakaʻuvea
	xav Xavánte - A’uwẽ
	zun Zuni - Shiwiʼma
- [ ] complete Arabic, Persian, and Malay sub-languages

## Other

- [ ] ask others to check non-done languages (Ukrainian, Russian, Albanian, Polish, Spanish, Italian, …)
- [ ] work on presentation
- [ ] consider including Extensis character sets
- [ ] consider including Speak Easy
- [ ] consider including Adobe spreadsheets
- [ ] punctuation used by a language
- [ ] list OpenType features needed to support a language with a brief note about what the feature should do.