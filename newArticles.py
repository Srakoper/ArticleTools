"""
Module for fetching new articles from a given timeframe and ouputting them as a database and .xls[x] file of new articles.
!!! Does not add new articles to the database of all articles! Use fetchURLs.py + articleFromHTML.py or concatenate database of new articles with all articles. !!!
Takes start and end dates of a timeframe in YYYY-M[M]-D[D] format, start <= end, or fetches articles from a previous day.
Saves fetched URLs to daily.txt.
Adds data from new articles to the daily.sqlite database and daily.xlsx file of new articles, which are created anew every time the program is run.
Dependencies: modules tagRelevance, tagSimilarity
"""

from datetime import datetime, date, timedelta
import urllib.request
from bs4 import BeautifulSoup as bs
import sqlite3
import openpyxl
import re
from time import time as t
from tagSimilarity import tagSimilarity
from tagRelevance import tagRelevance

class DateError(Exception):
    pass

def dateGenerator(begin, end):
    """
    Generates dates from a given time interval.
    :param begin: start of interval
    :param end: end of interval, end >= start
    :return: dates in YYY-MM-DD format from interval
    """
    current = begin
    while current <= end:
        yield current
        current += timedelta(days=1)

start = t()
"""
SQL table schema.
"""
connection = sqlite3.connect("daily.sqlite")
cursor = connection.cursor()
cursor.executescript("""
    DROP TABLE IF EXISTS Articles;
    DROP TABLE IF EXISTS Tags;
    DROP TABLE IF EXISTS Relations;

    CREATE TABLE Articles (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    idnum       INTEGER UNIQUE,
    address     TEXT,
    section     TEXT,
    author      TEXT,
    time        TEXT,
    title       TEXT,
    label       TEXT,
    lead        TEXT,
    content     TEXT,
    important   TEXT,
    tags        INTEGER,
    similarity  INTEGER,
    relevance   REAL);

    CREATE TABLE Tags (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    tag         TEXT UNIQUE);

    CREATE TABLE Relations (
    id_article  INTEGER,
    id_tag      INTEGER,
    PRIMARY KEY (id_article, id_tag))
    """)
"""
Fetching new URLs
"""
if input("Articles from yesterday? Y/N ") in ["Y", "y"]:
    begin_str = str(datetime.now().date() - timedelta(days=1))
    begin = [int(d) for d in begin_str.split("-")]
    begin_date = date(begin[0], begin[1], begin[2])
    end_date = begin_date
else:
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
fh = open("daily.txt", "w", encoding="UTF-8")
fh.write("URLs fetched on " + str(datetime.now()) + "\n")
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
"""
xls file
"""
wb = openpyxl.Workbook()
sheet = wb.active
try: sheet.title = end_str
except NameError: sheet.title = begin_str
counter = 1
"""
Parsing of articles from URLs.
"""
for line in open("daily.txt").readlines():
    if "http://" in line:
        try: html = urllib.request.urlopen(line.rstrip()).read()
        except urllib.error.HTTPError:
            open("articles_404.txt", "a", encoding="UTF-8").write(line[:-1])
            print("Article not found: " + line.rstrip())
            continue
        soup = bs(html, "html5lib") # html5lib OR lxml
        # address (url) of article
        address = line.rstrip()
        print(address)
        # article ID
        id = int(re.findall("\d+$", address)[0])
        # section of article
        try: section = re.findall("\.net/(.+)/", address)[0]
        except IndexError: section = ""
        # author(s) of article
        authors = list()
        authors.extend(re.findall(">(.*?)</h3>", str(soup.find_all("h3", class_="article__author_name"))))
        authors.extend(re.findall(">(.*?)</h3>", str(soup.find_all("h3", class_="article__authors_name"))))
        try: authors.insert(0, re.findall("<span>(.*?)</span>", str(soup.find_all("div", class_="article__promo")))[0])
        except IndexError: pass
        if not authors: authors = [""]
        # publication time of artice
        time = re.findall("(\d+-\d+-\d+)T", str(soup("time")[0]))[0]
        # article title
        title = re.findall(">(.*)<", str(soup("h1")[0]))[0]
        # article label
        label = re.findall(">(.*)<", str(soup("span", class_="article__label")[0]))[0]
        # article lead, text only, no urls
        try: lead = re.sub("<.+?>", "", re.findall(">(.*)<", str(soup("p")[0]))[0])
        except IndexError: lead = ""
        # main article content, text and headlines only, no urls, iframes
        content_lines = str(soup.find_all("div", class_="article__content")[0]).split("\n")
        content = str()
        pattern = re.compile("<.+?>")
        for line in content_lines:
            if "<div" not in line and "</div>" not in line and "<a href" not in line and "iframe" not in line: content += re.sub(pattern, "", line) + "\n"
        # important text (text in italic or bold)
        important_set = set()
        pattern = re.compile("<[se][tm]\w*>(.+?)</")
        for line in content_lines:
            if "<div" not in line and "</div>" not in line and "<a href" not in line and "iframe" not in line:
                for item in re.findall(pattern, line): important_set.add(item.replace("\xa0", " "))
        important = ", ".join(important_set)
        # entire article
        article = title + "\n\n" + label + "\n\n" + lead + "\n\n" + content
        # article tags
        tags = re.findall(">(.*?)</a>", str(soup.find_all("a", class_="tags__link")))
        # number of tags
        tag_number = len(tags)
        # tag similarity index
        similarity = tagSimilarity(tags)
        # tag relevance index
        relevance = tagRelevance(tags, important, article)
        # database builder
        cursor.execute("UPDATE Articles SET author = ? WHERE idnum = ?", (authors[0], id))
        cursor.execute("""INSERT OR IGNORE INTO Articles  (address,
                                                            idnum,
                                                            section,
                                                            author,
                                                            time,
                                                            title,
                                                            label,
                                                            lead,
                                                            content,
                                                            important,
                                                            tags,
                                                            similarity,
                                                            relevance)
                                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                                           (address,
                                                            id,
                                                            section,
                                                            authors[0],
                                                            time,
                                                            title,
                                                            label,
                                                            lead,
                                                            content,
                                                            important,
                                                            tag_number,
                                                            similarity,
                                                            relevance))
        cursor.execute("SELECT id FROM Articles WHERE idnum = ?", (id,))
        id_article = cursor.fetchone()[0]
        for tag in tags:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM Tags WHERE tag = ?)", (tag,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO Tags (tag) VALUES (?)", (tag,))
                cursor.execute("SELECT id FROM Tags WHERE tag = ?", (tag,))
                id_tag = cursor.fetchone()[0]
                cursor.execute("INSERT OR REPLACE INTO Relations (id_article, id_tag) VALUES (?, ?)", (id_article, id_tag))
            else:
                cursor.execute("SELECT id FROM Tags WHERE tag = ?", (tag,))
                id_tag = cursor.fetchone()[0]
                cursor.execute("INSERT OR REPLACE INTO Relations (id_article, id_tag) VALUES (?, ?)", (id_article, id_tag))
        connection.commit()
        # xls builder
        a = "A" + str(counter)
        b = "B" + str(counter)
        sheet[a] = address
        sheet[b] = authors[0]
        counter += 1
connection.close()
while True:
    try:
        wb.save("daily.xlsx")
        break
    except PermissionError: input("Please close daily.xlsx and press any key. ")

print("Finished in %s seconds." % "{0:.3f}".format(t() - start))