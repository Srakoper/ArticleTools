"""
Module for fetching URLs of articles from a given timeframe.
Takes start and end dates of a timeframe in YYYY-M[M]-D[D] format, start <= end.
Fetches URls of articles from a given timeframe and saves them in the articles.txt file.
"""

from datetime import date, datetime, timedelta
import urllib.request
from bs4 import BeautifulSoup as bs
import re
from time import time as t

class DateError(Exception):
    pass

def dateGenerator(begin, end):
    current = begin
    while current <= end:
        yield current
        current += timedelta(days=1)

"""
Fetching new URLs
"""
while True:
    try:
        begin_str = input("Enter a valid start date in YYYY-M-D format: ")
        assert re.search("\d{4}-\d+-\d+", begin_str)
        begin = [int(d) for d in begin_str.split("-")]
        begin_date = date(begin[0], begin[1], begin[2])
        begin_datetime = datetime(begin[0], begin[1], begin[2])
        break
    except AssertionError: print("Date not in required format. Enter a date in YYYY-M-D format.")
    except ValueError: print("Date not valid. Enter a valid date.")
while True:
    try:
        end_str = input("Enter a valid end date in YYYY-M-D format (end >= begin): ")
        assert re.search("\d{4}-\d+-\d+", end_str)
        end = [int(d) for d in end_str.split("-")]
        end_date = date(end[0], end[1], end[2])
        end_datetime = datetime(end[0], end[1], end[2])
        if int((end_datetime - begin_datetime).total_seconds()) < 0: raise DateError
        break
    except AssertionError: print("Date not in required format. Enter a date in YYYY-M-D format.")
    except ValueError: print("Date not valid. Enter a valid date.")
    except DateError: print("End date before start date. Enter valid end date.")
start = t()
fh = open("articles.txt", "a", encoding="UTF-8")
fh.write("\nURLs fetched on " + str(datetime.now()) + "\n")
fh.write("Articles from " + str(begin_date) + " to " + str(end_date) + "\n")
pattern = re.compile("href=\"(.+)\"\stitle")
for dt in dateGenerator(begin_date, end_date):
    print(dt)
    html = urllib.request.urlopen("http://siol.net/pregled-dneva/" + re.sub("-0", "-", str(dt)))
    soup = bs(html, "html5lib")  # html5lib OR lxml
    articles = re.findall(pattern, str(soup.find_all("ul", class_="timemachine__article_list")))
    for article in articles:
        fh.write("http://siol.net" + article + "\n")
fh.close()

print("Finished in %s seconds." % "{0:.3f}".format(t() - start))
print("URLs appended to articles.txt.")