"""
Module for building/extending a database of articles from Siol.net website.
Takes URLs of articles to add in a form of a .txt file as an input.
Fetches data from websites of given article URLs.
Adds data from articles not in database to the articles.sqlite database or ignores if article already in database.
Dependencies: modules tagRelevance, tagSimilarity
"""

import urllib.request
from bs4 import BeautifulSoup as bs
import re
import sqlite3
from datetime import date
from time import time as t
from hashlib import md5
from tagSimilarity import tagSimilarity
from tagRelevance import tagRelevance

# classes
class Article(object):
    """
    Article object for storing article data.
    """
    def __init__(self, idnum, address, section, author, coauthors, date, time, title, label, lead, content, important, tags, tag_number, similarity, relevance, views, shares, comments, hotness, refreshed):
        self.idnum = idnum
        self.address = address
        self.section = section
        self.author = author
        self.coauthors = coauthors
        self.date = date
        self.time = time
        self.title = title
        self.label = label
        self.lead = lead
        self.content = content
        self.important = important
        self.tags = tags
        self.tag_number = tag_number
        self.similarity = similarity
        self.relevance = relevance
        self.views = views
        self.shares = shares
        self.comments = comments
        self.hotness = hotness
        self.refreshed = refreshed
    def getIdnum(self): return self.idnum
    def getAddress(self): return self.address
    def getSection(self): return self.section
    def getAuthor(self): return self.author
    def getCoauthors(self): return self.coauthors
    def getDate(self): return self.date
    def getTime(self): return self.time
    def getTitle(self): return self.title
    def getLabel(self): return self.label
    def getLead(self): return self.lead
    def getContent(self): return self.content
    def getImportant(self): return self.important
    def getTags(self): return self.tags
    def getTagNumber(self): return self.tag_number
    def getSimilarity(self): return self.similarity
    def getRelevance(self): return self.relevance
    def getViews(self): return self.views
    def getShares(self): return self.shares
    def getComments(self): return self.comments
    def getHotness(self): return self.hotness
    def getRefreshed(self): return self.refreshed

class Comment(object):
    """
    Comment object for storing comment data.
    """
    def __init__(self, address, user, text, date, time, up, down, reply_to=None):
        self.address = address
        self.user = user
        self.text = text
        self.date = date
        self.time = time
        self.up = up
        self.down = down
        self.reply_to = reply_to
        self.hash_value = md5(bytes(user + text + date + time, encoding="UTF-8")).hexdigest() # attempts to create a unique value for comment based on its user, text, date and time
    def getAddress(self): return self.address
    def getUser(self): return self.user
    def getText(self): return self.text
    def getDate(self): return self.date
    def getTime(self): return self.time
    def getUp(self): return self.up
    def getDown(self): return self.down
    def setReplyTo(self, reply_to_comment): self.reply_to = reply_to_comment
    def getReplyTo(self): return self.reply_to
    def getHashValue(self): return self.hash_value

# functions
def getArticle(address, content, Article):
    """
    Gets article data from parsed HTML string and creates am Article object.
    :param address: str, article URL
    :param content: BS4 soup object
    :param Article: Article class
    :return: Article object
    """
    # article ID
    id = int(re.findall("\d+$", address)[0])
    # section of article
    try: section = re.findall("\.net/(.+)/", address)[0]
    except IndexError: section = ""
    # parsed article content
    soup = content
    # author(s) of article
    authors = list()
    authors.extend([author[:-1] if author[-1] == "," else author for author in re.findall("/\">(.+)", str(soup.find_all("span", class_="article__author")))])
    try: authors.insert(0, re.findall("<span>(.*?)</span>", str(soup.find_all("div", class_="article__pr_box")))[0])
    except IndexError: pass
    if not authors: authors = [""]
    if len(authors) > 1: coauthors = ", ".join(authors[1:])
    else: coauthors = ""
    authors = authors[0]
    # publication date of artice
    time = "-".join(reversed([datum if len(datum) > 1 else "0" + datum for datum in re.findall("(\d+)", soup.find("span", class_="article__publish_date--date").getText())]))
    # publication hour of article
    hour = ":".join([datum if len(datum) > 1 else "0" + datum for datum in re.findall("(\d+)", soup.find("span", class_="article__publish_date--time").getText())]) + ":00"
    # article title
    title = re.findall(">(.*)<", str(soup("h1")[0]))[0]
    # article label
    try: label = soup.find("span", class_="article__overtitle").getText()
    except AttributeError: label = ""
    # article lead, text only, no urls
    try: lead = re.sub("<.+?>", "", re.sub(r"\n\s{2,}", "", soup.find("div", class_="article__intro js_articleIntro").getText()))
    except IndexError: lead = ""
    # main article content, text and headlines only, no urls, iframes
    try: content_lines = soup.find("div", class_="article__main js_article js_bannerInArticleWrap").find_all("p")
    except RuntimeError: content_lines = []
    content = str()
    pattern = re.compile("<.+?>")
    for line in content_lines:
        if "<div" not in line and "</div>" not in line and "<a href" not in line and "iframe" not in line: content += re.sub(pattern, "", line.getText()) + "\n"
    content = re.sub(r"\n{2,}", "\n", content) # replaces multiple \n with single \n
    # important text (text in italic or bold)
    important_set = set()
    pattern = re.compile("<[se][tm]\w*>(.+?)</") # finds <strong> and <em> tags
    for line in content_lines:
        if "<div" not in line and "</div>" not in line and "<a href" not in line and "iframe" not in line:
            for item in re.findall(pattern, str(line)): important_set.add(item.replace("\xa0", " "))
    important = ", ".join(important_set)
    # entire article
    all = title + "\n\n" + label + "\n\n" + lead + "\n\n" + content
    # article tags
    tags = [tag.getText() for tag in soup.find_all("a", class_="article__tags--tag")]
    # number of tags
    tag_number = len(tags)
    # tag similarity index
    similarity = tagSimilarity(tags)
    # tag relevance index
    relevance = tagRelevance(tags, important, all)
    # article views
    try: pageviews = int(re.findall(r"\d+", str(soup("div", class_="article__views")))[0])
    except IndexError:
        try: pageviews = int(re.findall(r"\d+", re.findall(r"article__views.+<\/div>", str(soup))[0])[0])
        except IndexError: pageviews = 0
    # article shares
    try: shares = int(re.findall(r"\d+", str(soup("span", class_="article__total_shares")))[0])
    except IndexError: shares = 0
    # article comments number
    try: comments_number = int(re.findall(r"\d+", str(soup("span", class_="comments__post_count")))[0])
    except IndexError: comments_number = 0
    # article hotness
    try: hotness = float(soup.find("div", class_="article__hotness").find("span").getText().replace(",", "."))
    except (IndexError, AttributeError) as e: hotness = 0.0
    # refresh time of article data in database (last data update)
    refreshed = str(date.today())
    return Article(id, address, section, authors, coauthors, time, hour, title, label, lead, content, important, tags, tag_number, similarity, relevance, pageviews, shares, comments_number, hotness, refreshed)

def getComments(address, content, level, Comment):
    """
    Gets comments data from parsed HTML string and creates a Comment object.
    :param address: str, article URL
    :param content: BS4 element tag
    :param level: bool, True if comments on article page, False if separate page comments
    :param Comment: Comment class
    :return: list, Comment objects
    """
    comments = list()
    if level: comments_data = content.find_all("span", class_="comments__inner comments__inner--toplevel cf js_oneComment")
    else: comments_data = content.find_all("div", class_="comments__inner comments__inner--toplevel js_oneComment")
    for comment_data in comments_data:
        first_comment = None
        for i in range(len(comment_data.find_all("span", class_="comments__username"))):
            user = comment_data.find_all("span", class_="comments__username")[i].getText()
            text = comment_data.find_all("p", class_="comments__text")[i].getText()
            date_time = comment_data.find_all("span", class_="comments__timestamp")[i].getText()
            date = "-".join(re.findall(r"\d+(?=\.)", date_time)[::-1])
            time = re.findall(r"(?<=ob\s).+", date_time)[0] + ":00"
            try:
                votes = comment_data.find_all("span", class_="vote_count")
                up = int(votes[i*2].getText())
                down = int(votes[i*2+1].getText())
            except IndexError:
                up = None
                down = None
            comment_object = Comment(address, user, text, date, time, up, down)
            if i == 0:
                first_comment = comment_object.getHashValue()
                comments.append(comment_object)
            else:
                comment_object.setReplyTo(first_comment)
                comments.append(comment_object)
    return comments

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
    PRIMARY KEY (id_article, id_tag));

    CREATE TABLE IF NOT EXISTS Comments (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    id_article  INTEGER,
    address     TEXT,
    user        TEXT,
    text        TEXT,
    date        TEXT,
    time        TEXT,
    up          INTEGER,
    down        INTEGER,
    reply_to    TEXT,
    hash_value  TEXT UNIQUE)
    """)
"""
Parsing of articles from URLs.
"""
for line in open(input("Enter file name: ")).readlines():
    if "http://" in line or "https://" in line:
        ### modify all addresses from Gospodarstvo section to Posel danes section ###
        if "/gospodarstvo/" in line: line = line.replace("/novice/gospodarstvo/", "/posel-danes/novice/")
        ### end of modify ###
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
            print("Article not found: " + line.rstrip())
            continue
        soup = bs(html, "html5lib") # html5lib OR lxml
        # address (url) of article
        address = line.rstrip()
        print(address)
        # article
        article = getArticle(address, soup, Article)
        # article comments
        if not soup.find_all("div", class_="comments__show_all"):
            comments_soup = soup.find("ul", class_="comments__list cf")
            if comments_soup: comments = getComments(address, comments_soup, True, Comment)
            else: comments = []
        else:
            comments = getComments(address, soup.find("ul", class_="comments__list cf"), True, Comment) # gets 3 comments from article page, which contain votes
            comments_urls = ["https://siol.net" + soup.find_all("a", class_="comments__show_all--button")[0].get("href")]
            comments_html = urllib.request.urlopen(comments_urls[0]).read().decode("UTF-8")
            comments_soup = bs(comments_html, "html5lib")
            if comments_soup:
                multiple_urls = comments_soup.find_all("li", class_="pagination__item") # looks for possible URLs from multiple comments pages listed on a dedicated comments page
                if multiple_urls:
                    pages = 0
                    for url in reversed(multiple_urls):
                        page = url.find("a").getText()
                        if page:
                            pages = int(page)
                            break
                    for i in range(2, pages + 1): comments_urls.append(comments_urls[0] + "?page=" + str(i))
                for url in comments_urls:
                    url_html = urllib.request.urlopen(url).read().decode("UTF-8")
                    url_soup = bs(url_html, "html5lib")
                    comms = getComments(address, url_soup.find("ul", class_="comments__list cf "), False, Comment)
                    comments.extend(comms) # gets comments from dedicated page(s) (which also contain 3 comments from article page that are NOT duplicated in database)
        # database builder
        cursor.execute("UPDATE Articles SET author = ? WHERE idnum = ?", (article.getAuthor(), article.getIdnum()))
        cursor.execute("""INSERT OR IGNORE INTO Articles (address,
                                                          idnum,
                                                          section,
                                                          author,
                                                          coauthors,
                                                          time,
                                                          hour,
                                                          title,
                                                          label,
                                                          lead,
                                                          content,
                                                          important,
                                                          tags,
                                                          similarity,
                                                          relevance,
                                                          views,
                                                          comments,
                                                          shares,
                                                          hotness,
                                                          refreshed)
                                                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                                         (address,
                                                          article.getIdnum(),
                                                          article.getSection(),
                                                          article.getAuthor(),
                                                          article.getCoauthors(),
                                                          article.getDate(),
                                                          article.getTime(),
                                                          article.getTitle(),
                                                          article.getLabel(),
                                                          article.getLead(),
                                                          article.getContent(),
                                                          article.getImportant(),
                                                          article.getTagNumber(),
                                                          article.getSimilarity(),
                                                          article.getRelevance(),
                                                          article.getViews(),
                                                          article.getComments(),
                                                          article.getShares(),
                                                          article.getHotness(),
                                                          article.getRefreshed()))
        cursor.execute("SELECT id FROM Articles WHERE idnum = ?", (article.getIdnum(),))
        id_article = cursor.fetchone()[0]
        for tag in article.getTags():
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
        for comment in comments:
            cursor.execute("""INSERT OR IGNORE INTO Comments (id_article,
                                                              address,
                                                              user,
                                                              text,
                                                              date,
                                                              time,
                                                              up,
                                                              down,
                                                              reply_to,
                                                              hash_value)
                                                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                                             (id_article,
                                                              comment.getAddress(),
                                                              comment.getUser(),
                                                              comment.getText(),
                                                              comment.getDate(),
                                                              comment.getTime(),
                                                              comment.getUp(),
                                                              comment.getDown(),
                                                              comment.getReplyTo(),
                                                              comment.getHashValue()))
        connection.commit()
connection.close()

print("Finished in %s seconds." % "{0:.3f}".format(t() - start))