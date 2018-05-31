"""
Word tokenizer that strips words of capitalization, punctuation, spaces, and removes duplicates.
"""
from re import sub, search

stopwords = ("in", "ali", "k", "h", "s", "z", "pa", "o", "za", "pri", "po", "pred", "nad", "pod", "brez", "v", "iz",
             "na", "zaradi", "razen", "med", "a", "oziroma")
text = open("words_to_tokenize.txt").read().lower()
words = ", ".join(list(filter(lambda word: (word not in stopwords and len(word) > 2)
        and not search(r"[.,:;\?!<>\+'_()]", word) and not word.isdigit(),
        list(set(sub(r",", "", sub(r"\s{2,}", " ", sub(r"\n", " ", text))).split())))))
open("words_tokenized.txt", "w").write(words)
print("Tokenized words saved in words_tokenized.txt.")