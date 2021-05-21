# Comparison between Hyperglot and Unicode CLDR

The following comparison should be read bearing in mind the limits regarding specifying language support in terms of Unicode character code points. Naturally, there is more to full language support than lists of  code points. Even at the level of fonts.

## Unicode CLDR

[Unicode CLDR](http://cldr.unicode.org/) is the “most extensive standard repository of locale data available”. Among the data there are also *exemplar character sets* that can be potentially used to detect languages (e.g. check for language support in fonts).

An exemplar characters record corresponds to what is called an *orthography* in Hyperglot.

### Main issues

These are the main issues we see with the database (as of 21/5/2021):

- somewhat overengineered approach; the data is stored in many XML files with a complex structure
- the update process is slow and ineffective (via survey tool and vetting)
- sources for individual orthographies/languages are not referenced
- currently contains a lot of data dumps from other sources, a lot of unapproved data
- even approved orthographies sets often include characters that should not be present and miss characters that should be present
- required combinations for abugidas (e.g. conjuncts for Indian scripts) are missing
- there is no record regarding language-specific design requirements, i.e. local character forms
- there seems to be no way to track legacy orthographies, i.e. the development of the orthographies for a particular language cannot be documented using the database only
- searchable user-friendly presentation of the data is lacking/missing

In conclusion, although the database gives a sense of completeness, the orthographies cannot be relied upon when detecting language support.

## Hyperglot database

A lightweight database that focuses solely on listing characters used by a language. We have developed it since we were not content with the quality and structure of the data in Unicode CLDR and we tried to address the aforementioned issues.

### Main characteristics

- simple YAML file with relatively straightforward structure
- straightforward way to contribute using GitHub and open source
- very few mindless dumps, anything that has validity “” has been already checked with at least two online sources
- truly minimal approach, i.e. basic character sets do not include what is not considered a standard for a language, any characters used in loan words are strictly in the auxiliary set.
- marks are stored independently of the basic and auxiliary character sets
- uppercase is included (unlike in CLDR) to make the database less reliant on advanced post-processing and additional knowledge
- design notes and character alternates can be included to point out any language-specific design requirements that depart from (or go beyond) the Unicode standard
- multiple orthographies can be assigned to a single language-script combination
- includes own tool to use the data
- offers a searchable and user-friendly visual presentation of the data

### Current disadvantages

Those marked PLANNED are on the roadmap.

- while combinations of characters can be already included, the required combinations for abugidas (e.g. conjuncts for Indian scripts) are still missing. PLANNED.
- geographical location related to the use of the language is recorded only in notes, not systematically. (We do not currently consider it useful to include and it can be found in different databases.)
- punctuation at the level of script and/or language is missing. This is already present in the CLDR. PLANNED.
- numerals at the level of script and/or language. This is already present in the CLDR. PLANNED.
- ability to compare and export data in a form useful for the CLDR. PLANNED.
