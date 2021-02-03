# Compiling speakers data for Rosetta language database

For now we gather rudimentary language user data from various Wikipedia 
language pages.

## Setup

The language data is collected based on the languages defined in 
`/data/rosetta_new.yaml`. To run the scraper, use pip to install the required
libraries in `tools/speakers/requirements.txt`. 

## Scraping data

To collect fresh data, use:

```
cd tools/speakers
cp /dev/null "../../data/other/speakers.xml"
scrapy crawl speakers -o "../../other/users.xml"
```

To only test the spider, run as last command instead:

```
scrapy runspider speakers
```

To test data extraction from a page with URL run as last command instead (e.g. then in the shell use response.xpath(...) to test extraction):

```
scrapy shell URL
```

**NOTE:** That data is scraped raw data. You will almost always need to clean
it up manually in some way. The parsed data include the `speakers_raw` field 
for cross checking. Since we are searching Wikipedia not by the language ISO
code but by the **language name** it is entirely possible we will have misses
or mismatches of found language to language/ISO in our database.

One known issue is that for some languages Wikipedia will state eg. "300-450 
million users" - for which case we simply grab the first.

We also convert data like "4.1 million" or "4,100,100" to a plain integer.
Possibly malformed/inconsistently formatted data on Wikipedia (e.g. using comma
instead of period for million decimals/number pairing) might be a source for 
error.