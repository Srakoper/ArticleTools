"""
Module for building/extending a database of articles form an .xls[x] file.
Takes data from articles to add in a form of a .xls[x] file as an input. Such file must follow a predetermined schema.
Adds data from articles not in database to the articles.sqlite database or ignores if article already in database.
Ignores "important" field due to lack of formatted data from .xls[x] file.
Dependencies: modules tagRelevance, tagSimilarity
"""

import openpyxl
import sqlite3
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
    coauthors   TEXT,
    time        TEXT,
    title       TEXT,
    label       TEXT,
    lead        TEXT,
    content     TEXT,
    important   TEXT,
    tags        INTEGER,
    similarity  INTEGER,
    relevance   REAL);

    CREATE TABLE IF NOT EXISTS Tags (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    tag         TEXT);

    CREATE TABLE IF NOT EXISTS Relations (
    id_article  INTEGER,
    id_tag      INTEGER,
    PRIMARY KEY (id_article, id_tag))
    """)
"""
Parsing of articles from XLS file.
"""
wb = openpyxl.load_workbook(input("Enter file name: "), read_only = True, data_only=True)
articles = wb.get_sheet_by_name("Articles")
counter = 0
for row in articles.iter_rows(row_offset=1):
    if row[0].value:
        # address (url) of article
        address = "http://" + row[2].value
        # article ID
        id = int(row[0].value)
        # section of article
        try: section = row[7].value.lower() + "/" + row[8].value.lower()
        except AttributeError: section = ""
        # author(s) of article
        authors = list()
        authors.append(row[3].value)
        if row[4].value: authors.extend(row[4].value[1:].split("; "))
        # publication time of artice
        time = "-".join(reversed(row[1].value.split("/")))
        # article title
        title = row[9].value
        # article label
        label = row[11].value
        # article lead, text only, no urls
        lead = row[12].value
        # important text (empty)
        important = ""
        # main article content, text and headlines only, no urls, iframes
        content = row[13].value
        # entire article
        article = title + "\n\n" + label + "\n\n" + lead + "\n\n" + content
        # article tags
        tags = list()
        for i in range(16, 16 + int(row[15].value)):
            if i == 16: tags.append(str(row[i].value))
            else:
                try: tags.append(str(row[i].value[1:]))
                except TypeError: pass
        # number of tags
        tag_number = len(tags)
        # tag similarity index
        similarity = tagSimilarity(tags)
        # tag relevance index
        relevance = tagRelevance(tags, important, article)
        # database builder
        cursor.execute("""INSERT OR IGNORE INTO Articles   (address,
                                                            idnum,
                                                            section,
                                                            author,
                                                            time,
                                                            title,
                                                            label,
                                                            lead,
                                                            important,
                                                            content,
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
                                                            important,
                                                            content,
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
        counter += 1
        if counter % 100 == 0: print(counter)
    else: counter += 1
connection.close()

print("Finished in %s seconds." % "{0:.3f}".format(t() - start))