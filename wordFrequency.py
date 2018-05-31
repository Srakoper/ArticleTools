"""
Module for generating suggested tags for articles.
Takes URLs of articles to add in a form of a .txt file as an input.
Generates suggestions of tags with corresponding frequencies from the article, structured as:
    proposed names (sequences of capitalized words)
    proposed abbreviations (sequences of capital chars with length >= 2)
    proposed important text (bold or italic in article)
    proposed 3-word phrases
    proposed 2-word phrases
    proposed 1-word phrases with length > 3
    proposed 1-word phrases with length <= 3
Outputs suggestions for each article in the suggested.txt file.
"""

import re
import sqlite3
from time import time as t

def countFrequency(words, counter1, counter2=None):
    """
    Counts occurrences of single- or multi-word phrases in text, stores result in dict.
    """
    if counter2 == None:
        for word in words:
            if all(w.isupper() and len(w) == 1 or w[0].isupper() and not w.isupper() for w in word.split()): names[word] = names.get(word, 0) + 1 # finds suggested names
            else:
                phrase = word.lower()
                counter1[phrase] = counter1.get(phrase, 0) + 1
    else:
        for word in words:
            if len(word) > 1 and word.isupper(): abbreviations[word] = abbreviations.get(word, 0) + 1 # finds suggested abbreviations
            else:
                phrase = word.lower()
                try: int(phrase) # excludes numbers
                except ValueError:
                    if len(phrase) > 3: counter1[phrase] = counter1.get(phrase, 0) + 1
                    elif len(phrase) > 1: counter2[phrase] = counter2.get(phrase, 0) + 1

def sortFrequencies(counter, lst):
    """
    Sorts frequency dicts by frequency-phrase tuples, descending.
    """
    for word, frequency in counter.items():
        if frequency >= 1:
            lst.append((frequency, word))
    lst.sort(reverse=True)

def printFrequencies(lst, flag=False):
    """
    Prints frequencies, cutoff <= 10 except for names and abbreviations where there is no cutoff.
    """
    suggested = str()
    for i in range(len(lst)):
        if flag: suggested += str(lst[i][0]) + " " + str(lst[i][1]) + "\n"
        elif i < 10: suggested += str(lst[i][0]) + " " + str(lst[i][1]) + "\n"
    return suggested

start = t()
fh = open("suggested.txt", "a", encoding="UTF-8")
connection = sqlite3.connect("articles.sqlite")
cursor = connection.cursor()
for line in open(input("Enter file name: ")).readlines():
    if "http://" in line:
        id = int(re.findall("\d{6}", line)[0])
        cursor.execute("SELECT title, label, lead, content FROM Articles WHERE idnum = ?", (id,))
        text = re.sub("\s+", " ", " ".join(cursor.fetchone()))
        cursor.execute("SELECT important FROM Articles WHERE idnum = ?", (id,))
        important = re.sub(",\s", "\n", cursor.fetchone()[0])
        fh.write(line.rstrip() + "\n\n")
        names = dict()
        abbreviations = dict()
        three_words = dict()
        two_words = dict()
        one_word_long = dict()
        one_word_short = dict()
        names_list = list() # list of suggested names phrases (2 or 3-word phrases, first characters capitalized)
        abbreviations_list = list() # list of suggested abbreviations (single-word phrases, all characters capitalized)
        three_list = list() # list of 3-word phrases
        two_list = list() # list of 2-word phrases
        one_long_list = list() # list of single-word phrases, length > 3
        one_short_list = list() # list of single-word phrases, 1 < length <= 3
        pattern1 = re.compile(r"\b\w+\b")
        pattern2 = re.compile(r"\b\w+\W+\w+\b")
        pattern3 = re.compile(r"\b\w+\W+\w+\W+\w+\b")
        words_3 = re.findall(pattern3, text)
        words_3.extend(re.findall(pattern3, " ".join(text.split(" ")[1:])))
        words_3.extend(re.findall(pattern3, " ".join(text.split(" ")[2:])))
        words_2 = re.findall(pattern2, text)
        words_2.extend(re.findall(pattern2, " ".join(text.split(" ")[1:])))
        words_1 = re.findall(pattern1, text)
        countFrequency(words_3, three_words)
        countFrequency(words_2, two_words)
        countFrequency(words_1, one_word_long, one_word_short)
        sortFrequencies(names, names_list)
        sortFrequencies(abbreviations, abbreviations_list)
        sortFrequencies(three_words, three_list)
        sortFrequencies(two_words, two_list)
        sortFrequencies(one_word_long, one_long_list)
        sortFrequencies(one_word_short, one_short_list)
        fh.write("SUGGESTED NAMES\n")
        fh.write(printFrequencies(names_list, True))
        fh.write("\nSUGGESTED ABBREVIATIONS\n")
        fh.write(printFrequencies(abbreviations_list, True))
        fh.write("\nSUGGESTED IMPORTANT TEXT\n")
        fh.write(important + "\n")
        fh.write("\nTHREE-WORD PHRASES\n")
        fh.write(printFrequencies(three_list))
        fh.write("\nTWO-WORD PHRASES\n")
        fh.write(printFrequencies(two_list))
        fh.write("\nONE-WORD PHRASES, LENGTH > 3\n")
        fh.write(printFrequencies(one_long_list))
        fh.write("\nONE-WORD PHRASES, LENGTH <= 3\n")
        fh.write(printFrequencies(one_short_list))
        fh.write("\n\n")
fh.close()

print("Finished in %s seconds." % "{0:.3f}".format(t() - start))
