"""
Module for updating existing articles from a database.
Takes URLs of articles to update in a form of a .txt file as an input.
Fetches data from websites of given article URLs.
Updates (overwrites) data from all fields for a given database entry in the articles.sqlite database.
Dependencies: modules tagRelevance, tagSimilarity
"""

import urllib.request
from bs4 import BeautifulSoup as bs
import re
import sqlite3
from datetime import date
from time import time as t
from tagSimilarity import tagSimilarity
from tagRelevance import tagRelevance

start = t()

"""
SQL table schema.
"""
connection = sqlite3.connect("articles.sqlite")
cursor = connection.cursor()
cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Articles (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    idnum       INTEGER UNIQUE,
    address     TEXT,
    section     TEXT,
    author      TEXT,
    time        TEXT,
    hour        TEXT,
    title       TEXT,
    label       TEXT,
    lead        TEXT,
    content     TEXT,
    important   TEXT,
    tags        INTEGER,
    similarity  INTEGER,
    relevance   REAL,
    views       INTEGER,
    comments    INTEGER,
    shares      INTEGER,
    hotness     REAL,
    refreshed   TEXT);

    CREATE TABLE IF NOT EXISTS Tags (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    tag         TEXT UNIQUE);

    CREATE TABLE IF NOT EXISTS Relations (
    id_article  INTEGER,
    id_tag      INTEGER,
    PRIMARY KEY (id_article, id_tag))
    """)

"""
Parsing of articles from URLs.
"""
def removeArticle(line):
    """
    Removes article from database if article not found.
    :return:
    """
    open("articles_404.txt", "a", encoding="UTF-8").write(line)
    cursor.execute("SELECT id FROM Articles WHERE idnum = ?", (int(re.findall("\d+$", line.rstrip())[0]),))
    try:
        id_article = cursor.fetchone()[0]
        cursor.execute("SELECT id_tag FROM Relations WHERE id_article = ?", (id_article,))
        id_tags = cursor.fetchone()
        cursor.execute("DELETE FROM Articles WHERE id = ?", (id_article,))
        cursor.execute("DELETE FROM Relations WHERE id_article = ?", (id_article,))
        try:
            for id_tag in id_tags:
                cursor.execute("SELECT id_tag FROM Relations WHERE id_tag = ?", (id_tag,))
                if cursor.fetchone()[0] == 0: cursor.execute("DELETE FROM Tags WHERE id = ?", (id_tag,))
        except: pass
        connection.commit()
        print("Article not found and removed from database: " + line.rstrip())
    except TypeError: print("Article not found but not in database: " + line.rstrip())

for line in open(input("Enter file name: ")).readlines():
    if "http://" in line:
        tries = 0
        while True: # trying to open article 5 times before removing it from database
            try:
                html = urllib.request.urlopen(line.rstrip()).read().decode("UTF-8")
                tries = 0
                break
            except urllib.error.HTTPError:
                tries += 1
                print("Failed to open article {} {} times.".format(line.rstrip(), tries))
            if tries == 5: break
        if tries:
            removeArticle(line) # removes articles with 404 error
            continue
        soup = bs(html, "html5lib") # html5lib OR lxml
        # address (url) of article
        try:
            address = re.findall("http:\/\/siol[^\"]+", str(soup.find_all("meta")))[0]
            print(address)
        except IndexError:
            removeArticle(line) # removes articles w/o 404 error but redirected to section website
            continue
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
        # publication hour of article
        hour = re.findall("T(\d+:\d+:\d+)", str(soup("time")[0]))[0]
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
        # article views
        try: pageviews = int(re.findall(r"\d+", str(soup("div", class_="article__views")))[0])
        except IndexError:
            try: pageviews = int(re.findall(r"\d+", re.findall(r"article__views.+<\/div>", str(soup))[0])[0])
            except IndexError: pageviews = 0
        # article comments
        try: comments = int(re.findall(r"\d+", str(soup("span", class_="comments__post_count")))[0])
        except IndexError: comments = 0
        # article shares
        try: shares = int(re.findall(r"\d+", str(soup("span", class_="article__total_shares")))[0])
        except IndexError: shares = 0
        # article hotness
        try: hotness = float(soup.find("div", class_="article__hotness").find("span").getText().replace(",", "."))
        except IndexError: hotness = 0.0
        # refresh time of article data in database (last data update)
        refreshed = str(date.today())
        # database updater
        cursor.execute("""UPDATE Articles SET address = ?,
                                              idnum = ?,
                                              section = ?,
                                              author = ?,
                                              time = ?,
                                              hour = ?,
                                              title = ?,
                                              label = ?,
                                              lead = ?,
                                              content = ?,
                                              important = ?,
                                              tags = ?,
                                              similarity = ?,
                                              relevance = ?,
                                              views = ?,
                                              comments = ?,
                                              shares = ?,
                                              hotness = ?,
                                              refreshed = ?
                                              WHERE idnum = ?""",
                                             (address,
                                              id,
                                              section,
                                              authors[0],
                                              time,
                                              hour,
                                              title,
                                              label,
                                              lead,
                                              content,
                                              important,
                                              tag_number,
                                              similarity,
                                              relevance,
                                              pageviews,
                                              comments,
                                              shares,
                                              hotness,
                                              refreshed,
                                              id))
        cursor.execute("SELECT id FROM Articles WHERE idnum = ?", (id,))
        id_article = cursor.fetchone()[0]
        for tag in tags:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM Tags WHERE tag = ?)", (tag,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT OR IGNORE INTO Tags (tag) VALUES (?)", (tag,))
                cursor.execute("SELECT id FROM Tags WHERE tag = ?", (tag,))
                id_tag = cursor.fetchone()[0]
                cursor.execute("INSERT OR REPLACE INTO Relations (id_article, id_tag) VALUES (?, ?)", (id_article, id_tag))
            else:
                cursor.execute("SELECT id FROM Tags WHERE tag = ?", (tag,))
                id_tag = cursor.fetchone()[0]
                cursor.execute("INSERT OR REPLACE INTO Relations (id_article, id_tag) VALUES (?, ?)", (id_article, id_tag))
        connection.commit()
connection.close()

print("Finished in %s seconds." % "{0:.3f}".format(t() - start))