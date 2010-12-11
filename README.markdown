## Interpol Scraper ##

Web scraper for scraping the interpol 'red list'.  

The scraper itself requires Redis (for running more than one scraper at a time) and BeautifulSoup (for parsing the HTML).

Run `python scraper.py -h` for usage, or read the source (it's not beautiful, but it works). 

Also included is the results as of 09/12/2010 and the json file I exported from google refine after cleaning the data somewhat.

The cleaning isn't perfect either, so please update it if you can improve on it at all.