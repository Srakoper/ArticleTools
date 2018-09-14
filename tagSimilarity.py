"""
Module for computing tag similarity index. See details in method specification below.
"""

import difflib

tags = ['Aleksander Čeferin', 'Nogometna zveza Slovenija', 'UEFA', 'FIFA', 'Janez Janša', 'Zoran Janković', 'Igor Bavčar', 'Boštjan Jazbec', 'Boris Popovič', 'Rudi Zavrl', 'Ivan Simič', 'Michael van Praag', 'Angel Maria Villar Llona', 'Zvonimir Boban', 'Davor Šuker', 'Jure Janković', 'Borut Pahor', 'Janez Drnovšek', 'Boško Šrot', 'Dari Južna', 'Lionel Messi', 'Barcelona', 'Real Madrid', 'Hajduk Split', 'Gianni Infantino', 'Sepp Blatter', 'Michel Platini', 'Dejan Stefanović', 'Simona Dimic', 'Franc Kangler', 'Danilo Türk', 'Alenka Bratušek']
def tagSimilarity(tags):
    """
    Computes similarity index between any pair of tags except self. If similarity > boundary (0.75 by default), then score += 1.
    Uncomment variable similar, 2 add operations, and print statement to enable storing and displaying similar tags.
    :param tags: list of tags
    :return: similarity index (number of tag pairs with too large similarity)
    """
    score = 0
    # similar = set()

    for i in range(len(tags)):
        for j in range(len(tags)):
            if i != j and difflib.SequenceMatcher(None, tags[i].lower(), tags[j].lower()).ratio() > 0.75:
                score += 1
                # similar.add(tags[i])
                # similar.add(tags[j])
    # print(similar)
    return score // 2 # divided by 2 because of duplicate entries