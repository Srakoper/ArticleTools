"""
Module for finding articles that do not exist/cannot be reached (HTTPError).
Takes URLs of articles to add in a form of a .txt file as an input.
Finds articles that do not exist/cannot be reached and saves them in the articles_404.txt file.
Due to a possible large number of URLs to check and long running time of the program, a print statement prompts whenever 100 articles have been checked.
"""

import urllib.request

lines = open(input("Enter file name: ")).readlines()
for i in range(len(lines)):
    if i % 100 == 0: print(i)
    try: urllib.request.urlopen(lines[i].rstrip())
    except urllib.error.HTTPError:
        open("articles_404.txt", "a", encoding="UTF-8").write(lines[i])
        print("Article not found: " + lines[i].rstrip())