__doc__ = """
A scrapy spider for gathering language speaker data from Wikipedia language
pages
"""

__copyright__ = "Copyright (c) 2019, Rosetta Type. All rights reserved."

__author__ = "Johannes Neumeier"

import re
import yaml
import scrapy
import os


class LanguageSpider(scrapy.Spider):
    name = 'speakers'

    # Keep a dict of scraping URLs and their respective language code from
    # our data, to log our language tag to the gathered data
    urls = {}

    # Fetch the languages we want to gather speaker info about
    rosetta_yaml = os.path.join(os.path.dirname(__file__), "../../../../",
                                "data/rosetta_new.yaml")

    # We just paste the language name into the URL and hope for a
    # reasonable from wikipedia
    # The info we are interested in is usually found in a table.infobox on the
    # righthand side of the page. We are searching for tr elements with certain
    # text (label) and then parse that row's data (text)
    base = "https://en.wikipedia.org/wiki/%s_language"

    with open(rosetta_yaml, 'r') as stream:
        try:
            data = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        for script, languages in data.items():
            for key, lang in languages.items():
                urls[key] = base % lang["name"].replace(" ", "_")

    start_urls = [u for u in urls.values()]

    def parse(self, response):
        try:
            lang = [key for key, url in self.urls.items() if url ==
                    response.request.url][0]
        except Exception as e:
            lang = "unknown"

        # 'Native speakers' seems to be a Wikipedia standard label for language
        # pages
        speakers_xpath = "//table[contains(@class, 'infobox')]//tr[contains(.//div, 'Native speakers')]/td//text()"
        speakers_raw = " ".join(response.xpath(speakers_xpath).getall())
        speakers = speakers_raw.strip()

        if speakers is not None and speakers not in ["", "None", "none"]:

            # Remove anything before and after the first essential number, and
            # save that number with period and commans
            numbers = re.findall(r"^[^0-9]*([0-9,\.]*)\s?(million|billion)?",
                                 speakers.lower())[0]

            number = numbers[0].replace(",", "")

            # Parse "b/millions" to actual number:
            # To float, make m/billions, loose comma
            if numbers[1] == "billion":
                number = int(float(number) * 10 ** 9)

            if numbers[1] == "million":
                number = int(float(number) * 10 ** 6)

            # Plain numbers, no comma-formatting, no fractional humans please
            speakers = int(number)
        else:
            speakers = "unknown"

        # While we are at it try to fetch language codes to cross-reference
        iso_639_1 = response.xpath(
            "//table[contains(@class, 'infobox')]//tr[contains(.//a, 'ISO 639-1')]/td//a/text()").get()
        iso_639_2 = response.xpath(
            "//table[contains(@class, 'infobox')]//tr[contains(.//a, 'ISO 639-2')]/td//a/text()").get()

        yield {
            "lang": lang,
            "speakers": speakers,
            "speakers_raw": speakers_raw,
            "iso_639_1": iso_639_1,
            "iso_639_2": iso_639_2,
            "source": response.request.url
        }
