"""
A naive word conjugator of Slovene nouns and adjectives.
Tries to differentiate between masculine, feminine and neutral cases but will fail on certaine xceptions.
"""

def conjugate(word):
    """
    Conjugates word and returns its conjugations. Differentiates naively between masculine, feminine and neutral cases.
    :param word: word to conjugate
    :return: conjugations of word
    """
    # feminine case
    if word[-1] == "a":
        root = word[:-1]
        if word[-3:] in ["lna", "ska", "čna", "sna", "šna", "ška", "mna", "tna"]: return [word, root + "e", root + "i", root + "o", root + "im", root + "ih", root + "imi"]
        else:
            conjugated = [word, root + "e", root + "i", root + "o", root + "am", root + "ah", root + "ami"]
            if root[-1] == "l": conjugated.append(root[:-1] + "e" + root[-1])
            elif root[-1] == "j" and root[-2] not in consonants and root[-3] not in ["a", "e", "i", "o", "u"]: conjugated.append(root[:-2] + "e" + root[-2:])
            else: conjugated.append(root)
            return conjugated
    # neutral case
    if word[-1] == "o":
        root = word[:-1]
        if word[-3:] in ["rno", "sko", "ško", "lno", "čno", "sno", "šno"]: return [word, root + "ega", root + "emu", root + "em", root + "im", root + "i", root + "ih", root + "imi"]
        else: return [word, root, root + "a", root + "u", root + "om", root + "ih", root + "i"]
    elif word[-1] == "e":
        root = word[:-1]
        return [word, root, root + "a", root + "u", root + "em", root + "ih", root + "i"]
    # masculine case
    if word[-1] not in consonants:
        if word[-2:] in ["šč", "ec"]:
            root = word[:-2] + word[-1]
            return [word, root + "a", root + "u", root + "em", root + "i", root + "ev", root + "e", root + "ih"]
        elif (len(word) >= 5 and word[-2:] == "ek") or (len(word) >= 4 and word[-4:] in ["eter", "ster"] or word[-3:] == "zem"):
            root = word[:-2] + word[-1]
            return [word, root + "a", root + "u", root + "om", root + "i", root + "ov", root + "e", root + "ih"]
        elif word[-1] == "r": return [word, word + "ja", word + "ju", word + "jem", word + "ji", word + "jev", word + "je", word + "jih"]
        elif word[-1] == "j": return [word, word + "a", word + "u", word + "em", word + "i", word + "ev", word + "e", word + "ih"]
        else: return [word, word + "a", word + "u", word + "om", word + "i", word + "ov", word + "e", word + "ih"]
    if word[-1] == "i":
        root = word[:-1]
        return [word, root + "ega", root + "emu", root + "em", root + "im", root + "ih", root + "imi"]

words = open("words_to_conjugate.txt").read().replace(" ", "").split(",")
consonants = ["a", "e", "i", "o", "u"]
conjugations = list()
for word in words: conjugations.extend(conjugate(word))
#print(conjugations)
open("words_conjugated.txt", "w").write(", ".join(conjugations))
print("Conjugated words saved in words_conjugated.txt")