# TODO

@Johannes

- [x] double check if YAML is well formed, list-type fields are always lists etc.
- [ ] add language names where missing or where -- is used
- [x] add speaker counts where missing or where -- is used
- [x] add a date (year) for the speaker count information, to the field `speakers_date`.
- [x] compare scraped speaker counts with those currently in the DB: this could lead to improved regular expression and migh help us update the existing counts in the DB. I would prefer to do this manually.
- [x] add langtool, refactor to work with the new format
- [x] langtool should subset the rosetta.yaml per font
- [x] check if all macrolanguages have been covered, i.e. if all ISO 639-3 languages marked as macrolanguages have a non-empty `includes` field. List those that do not.
	- NOTE: Currently also cross-checking iso data against rosetta data and emitting a warning if the rosetta data is missing one of those macrolanguages altogether
- [x] check if all names are iso-639-3, print output. The update might need to be done manually not to overwrite our preferred names.
	- NOTE: The only two cases of difference were quotes: 'Ta’izzi-Adeni Arabic' (iso: 'Ta'izzi-Adeni Arabic') and 'Ga’anda' (iso:'Ga'anda')
- [x] make sure characters used in autonyms are also in the base for corresponding orthography
- [x] add licence to this repo
- [x] sort rosetta.yaml dict by key a-z
- [x] CLI option to pass several files and compute union (and why not also intersect) of supported languages

Notes:

- name and autonym of an orthography override those of languages (probably not needed now)
- [ ]if there is not any orthography for a language, check if there is a macrolanguage which includes this language with some orthography. If so, use that.
- [x] when checking for language support in a font, ignore entries with `todo_status: todo`, set aside those with `todo_status: weak`. 
- [ ] Ignore orthographies with `status: historical` and provide switch to ignore languages with status `historical` or `constructed`, but include by default.

@David

- [x] check if all macrolanguages have been covered, i.e. if all ISO 639-3 languages marked as macrolanguages have a non-empty `includes` field. List those that do not.
- [x] check if all names are iso-639-3, print output. The update might need to be done manually not to overwrite our preferred names.
- [x] make sure characters used in autonyms are also in the base for corresponding orthography
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
	- [ ] include punctuation in checking that an autonym can be spelled in its provided orthography
- [ ] list OpenType features needed to support a language with a brief note about what the feature should do.

## Double check those errors:

- 'aao' has an orthography which is missing a 'base' attribute
- 'abh' has an orthography which is missing a 'base' attribute
- 'abv' has an orthography which is missing a 'base' attribute
- 'acm' has an orthography which is missing a 'base' attribute
- 'acq' has an orthography which is missing a 'base' attribute
- 'acw' has an orthography which is missing a 'base' attribute
- 'acx' has an orthography which is missing a 'base' attribute
- 'acy' has an orthography which is missing a 'base' attribute
- 'adf' has an orthography which is missing a 'base' attribute
- 'aeb' has an orthography which is missing a 'base' attribute
- 'aec' has an orthography which is missing a 'base' attribute
- 'afb' has an orthography which is missing a 'base' attribute
- 'aiq' has an orthography which is missing a 'base' attribute
- 'ajp' has an orthography which is missing a 'base' attribute
- 'apc' has an orthography which is missing a 'base' attribute
- 'apd' has an orthography which is missing a 'base' attribute
- 'arb' has an orthography which is missing a 'base' attribute
- 'arq' has an orthography which is missing a 'base' attribute
- 'ars' has an orthography which is missing a 'base' attribute
- 'ary' has an orthography which is missing a 'base' attribute
- 'arz' has an orthography which is missing a 'base' attribute
- 'auz' has an orthography which is missing a 'base' attribute
- 'avl' has an orthography which is missing a 'base' attribute
- 'ayh' has an orthography which is missing a 'base' attribute
- 'ayl' has an orthography which is missing a 'base' attribute
- 'ayn' has an orthography which is missing a 'base' attribute
- 'ayp' has an orthography which is missing a 'base' attribute
- 'bbz' has an orthography which is missing a 'base' attribute
- 'deh' has an orthography which is missing a 'base' attribute
- 'haz' has an orthography which is missing a 'base' attribute
- 'pes' has an orthography which is missing a 'base' attribute
- 'pga' has an orthography which is missing a 'base' attribute
- 'phv' has an orthography which is missing a 'base' attribute
- 'prs' has an orthography which is missing a 'base' attribute
- 'shu' has an orthography which is missing a 'base' attribute
- 'ssh' has an orthography which is missing a 'base' attribute
- 'urd' has an orthography which is missing a 'base' attribute
- 'bhh' has an orthography which is missing a 'base' attribute
- 'bhh' has an orthography which is missing a 'base' attribute
- 'ems' has an orthography which is missing a 'base' attribute
- 'uzs' has an orthography which is missing a 'base' attribute
- 'ydd' has an orthography which is missing a 'base' attribute
- 'yih' has an orthography which is missing a 'base' attribute
- 'sjk' has an orthography which is missing a 'base' attribute
- 'sia' has an orthography which is missing a 'base' attribute

- 'abk' has invalid autonym 'Аҧсшәа‎' which cannot be spelled with that orthography's charset 'ҵнучҩҿлқжҟҳыдрию тксщџӷзҷԥаяәҭецэӡбгшмфхҽйоъпвь' - missing 'ҧ'
- 'crh' has invalid autonym 'Qırımtatar tili' which cannot be spelled with that orthography's charset 'maocpi jçwdlsvfğekgşbzöüqtrunhñxy' - missing 'ı'
- 'dlg' has invalid autonym 'Дулҕан' which cannot be spelled with that orthography's charset 'нучлӈжүыдрию тксщзаяецэёөбгшмфхйоъпвһь' - missing 'ҕ'
- 'jdt' has invalid autonym 'Juwri' which cannot be spelled with that orthography's charset 'ִַבזצתחכעקש לי׳נרהאפָמגוסדּ' - missing 'rjuwi'
- 'kur' has invalid autonym 'Kurdî' which cannot be spelled with that orthography's charset 'нучлждри ӧтксщԝԛзаәецэбгшмфхйопвһь' - missing 'rkudî'
- 'kur' has invalid autonym 'Kurdî' which cannot be spelled with that orthography's charset 'méùaíocpi j'wdlsvfekgbzqtrúunhxy' - missing 'î'
- 'oaa' has invalid autonym 'Уйльта' which cannot be spelled with that orthography's charset 'нучлӈждрӣ тксзјӣаеэӡөбԩгмфхопв' - missing 'йь'
- 'ron' has invalid autonym 'Română' which cannot be spelled with that orthography's charset 'нучлжыдрию тксӂзаяецэбгшмфхйопвь' - missing 'mârnăo'
- 'tly' has invalid autonym 'Толыши' which cannot be spelled with that orthography's charset 'нучлждри тксзјаәецбгшмфҹҝхйопвһғ' - missing 'ы'
- 'uzn' has invalid autonym 'Ўзбекча' which cannot be spelled with that orthography's charset 'ӯнучлқжҳыдрию тксщзаяецэёбгшмфхйоъпвьғ' - missing 'ў'
- 'aat' has invalid autonym 'Αρβανίτικα' which cannot be spelled with that orthography's charset 'οαξμδικπβ γϳυχdτζ̱̇σbλρ̈ενφθ' - missing 'ί'
- 'bem' has invalid autonym 'Chibemba' which cannot be spelled with that orthography's charset 'maocpi jwdlsvfekgbtuny' - missing 'h'
- 'fao' has invalid autonym 'Føroyskt' which cannot be spelled with that orthography's charset 'maíocpi jwdlsvfåekgóýbðzöqtrúunæhxáy' - missing 'ø'
- 'haa' has invalid autonym 'Häł gołan' which cannot be spelled with that orthography's charset 'maocpài jäwdląsvfâekgbǎzqtrëunhxy' - missing 'ł'
- 'hop' has invalid autonym 'Hopilàvayi' which cannot be spelled with that orthography's charset 'maocpi jwdlsvfekgbzöqtrunhxy' - missing 'à'
- 'mgo' has invalid autonym 'Mɨta’' which cannot be spelled with that orthography's charset 'mùaocpàiè jŋʼwds̀fekgbɔzòtrunìhyə' - missing 'ɨ'
- 'ruo' has invalid autonym 'Rumârește' which cannot be spelled with that orthography's charset 'mașăocpiľ jwdlsvfåekgbzńqtrunhxyț' - missing 'â'
- 'sjt' has invalid autonym 'Са̄мькӣлл' which cannot be spelled with that orthography's charset 'ӆнучлӈжыдрию тксщӭзјӊая’ецӓэёбҏгшмфҍхӎйоъпвҋһь' - missing 'ӣ'
- 'srm' has invalid autonym 'Saamáka' which cannot be spelled with that orthography's charset 'maocpi jwdlsvfekgbzöqtrëunhxy' - missing 'á'
- 'xav' has invalid autonym 'A’uwẽ' which cannot be spelled with that orthography's charset 'méaocpi jwĩdlõsvfekgbzôöãqtrunhxy' - missing 'ẽ'

- Included language 'nno' not found in data
- 'nor' has invalid included languages