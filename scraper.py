"""
Scraper for interpol 'red list'.

Hacked together
"""

import sys
import urllib2
import re
import csv
import StringIO
from optparse import OptionParser

import redis
import BeautifulSoup

r = redis.Redis()

class Scraper():
    def __init__(self):
        self.soup = None


    def get_url(self, url, post={}):
        """
        Take a URL, request it and turn it in to a soup object.
        """
        r = urllib2.urlopen(url, data=post)
        self.soup = BeautifulSoup.BeautifulSoup(r)
        return self.soup


    def parse_results(self):
        """
        Parses a results page in to a set of hrefs to scrape later.
        """

        results = self.soup.findAll('a', href=re.compile("/public/Data/Wanted/Notices/Data", re.I))
        notices = set()
        for result in results:
            notices.add(result['href'])
        return notices


    def parse_list(self):
        """
        Pages through the search results.
        """

        if not self.soup:
            raise ValueError("No soup object, has the initial search been performed?")

        notices = set()

        # Parse the first page
        page_results = self.parse_results()
        notices.update(page_results)

        # Page through results
        for page in self.soup.findAll('a', href=re.compile('ResultListNew.asp')):
            url = "http://www.interpol.int/Public/Wanted/Search/"+page['href']
            self.get_url(url)
            page_results = self.parse_results()
            notices.update(page_results)

        self.notices = notices
        return notices


    def parse_notices(self, url=None):
        url = "http://www.interpol.int"+notice
        print url
        self.get_url(url)
        record = []
        record.append(self.parse_field("Present family name:")     )
        record.append(self.parse_field("Forename:")                )
        record.append(self.parse_field("Sex:")                     )
        record.append(self.parse_field("Date of birth:")           )
        record.append(self.parse_field("Place of birth:")          )
        record.append(self.parse_field("Language spoken:")         )
        record.append(self.parse_field("Nationality:")             )
        record.append(self.parse_field("Categories of Offences:")  )
        record.append(self.parse_field("Arrest Warrant Issued by:"))
        record.append(url)

        output = StringIO.StringIO()
        writer = csv.writer(output)
        writer.writerow(record)
        output.flush()
        output.seek(0,0)
        return url, output.next()


    def parse_field(self, text):
        """
        Searches for 'text' and returns the text of the next td found.
        
        If nothing is found, return an empty string.
        """
        try:
            return self.soup.find(text=text).findNext('td').text
        except:
            return ''



parser = OptionParser()
parser.add_option("-l", "--list", action="store_true", dest="list",
                  help="parse the list and add it to the redis queue")
parser.add_option("-n", "--notices", action="store_true", dest="notices",
                  help="parse the notices from the list")
parser.add_option("-e", "--export", action="store_true", dest="export",
                  help="Export everything in the redis hash to stdout")

(options, args) = parser.parse_args()

search_url = "http://www.interpol.int/Public/Wanted/Search/ResultListNew.asp?EntityName=&EntityForename=&EntityNationality=&EntityAgeBetween=15&EntityAgeAnd=95&EntitySex=&EntityEyeColor=&EntityHairColor=&EntityOffence=&ArrestWarrantIssuedBy=&EntityFullText=&cboNbHitsPerPage=500&cboNbPages=5000&Search=Search"
# Fewer results, for testing:
# search_url = "http://www.interpol.int/Public/Wanted/Search/ResultListNew.asp?EntityName=&EntityForename=&EntityNationality=&EntityAgeBetween=15&EntityAgeAnd=95&EntitySex=&EntityEyeColor=&EntityHairColor=&EntityOffence=&ArrestWarrantIssuedBy=&EntityFullText=&cboNbHitsPerPage=20&cboNbPages=1&Search=Search"

s = Scraper()
if options.list:
    print "getting url"
    s.get_url(search_url)
    print "parsing list"
    for notice in s.parse_list():
        r.sadd('interpol_notices', notice)

if options.notices:
    print "parsing notices"
    while r.scard('interpol_notices'):
        notice = r.spop('interpol_notices')
        try:
            k,v = s.parse_notices(notice)
            r.hset('interpol_results', k, v)
        except KeyboardInterrupt:
            r.sadd('interpol_notices', notice)
            break
        except Exception, e:
            print e
            r.sadd('interpol_notices', notice)

if options.export:
    for row in r.hgetall('interpol_results'):
        print r.hget('interpol_results', row).strip()

