"""
Module for computing tag relevance index. See details in method specification below.
"""

import re

def tagRelevance(tags, important, article):
    """
    Computes relevance index for tags and corresponding article.
    :param tags: list of tags
    :param important: list of important keywords
    :param article: text of entire article
    :return: relevancy index
    """
    score = 1 # score is decreased by penalty for each tag not found in article and increased by 0.1 for each tag found in important text (thus 0 > score >= 1)
    try: penalty = 1 / len(tags)
    except ZeroDivisionError: return 0
    for tag in tags:
        regex_string = ""
        split = tag.split()
        for string in split:
            if "(" in string: string = string.replace("(", "\(")
            if ")" in string: string = string.replace(")", "\)")
            if "*" in string: string = string.replace("*", "\*")
            if len(string) > 3: regex_string += string[:-2] + "\w+\s"
            else: regex_string += string + "\s"
        pattern = re.compile(regex_string[:-2], re.IGNORECASE)
        if not re.search(pattern, article): score -= penalty
    return score

# if important and re.search(pattern, important): score += 0.1