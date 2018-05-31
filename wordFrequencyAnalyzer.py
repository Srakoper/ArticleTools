"""
Computes word frequencies for words in articles from a given period (excluding stopwords).
Stopwords can be selected between regular Slovenian stopwords (stopwords1) and Graphite Adserver stopwords (stopwords2).
Default: stopwords2
Words are multiplied by the number of article pageviews, giving total number of impressions for each word, or by hotness score, or counted without multiplier.
Top 500 most frequent words are output as a TXT file.
"""
import re
import sqlite3
from nltk.tokenize import word_tokenize
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import date, datetime
from time import time as t

class DateError(Exception):
    pass

def binarySearch(iterable, item):
    """
    Performs a binary search on a sorted iterable.
    !!! Requires a sorted iterable. !!!
    :param iterable: iterable to search
    :param item: item to search for
    :return: if item found: item; if item not found: False
    """
    low = 0
    high = len(iterable)
    while high > low:
        mid = (low + high) // 2
        if iterable[mid] == item: return item
        elif iterable[mid] < item: low = mid + 1
        else: high = mid
    return False

while True:
    choice_menu = input("{}{}{}{}".format("1: analyze word frequencies for ALL articles in database\n",
                                          "2: analyze articles from a given period\n",
                                          "3: specify custom query WHERE clause (articles)\n",
                                          "4: specify custom query WHERE clause (comments)\n",
                                          "X: exit\n"))
    if choice_menu in ("1", "2", "3", "4", "X", "x"): break
    else: print("\nPlease enter a valid choice.\n\n")
if choice_menu == "X" or choice_menu == "x": quit()
else:
    while True:
        choice_multiplier = input("{}{}{}".format("1: use article pageviews as multiplier\n",
                                                  "2: use article hotness as multiplier\n",
                                                  "3: no multiplier\n"))
        if choice_multiplier in ("1", "2", "3"): break
    while True:
        choice_wordcloud = input("{}{}".format("1: create a word cloud image for selection\n",
                                               "2: no word cloud image\n"))
        if choice_wordcloud in ("1", "2"): break
    if choice_multiplier == "1": multiplier = "views"
    elif choice_multiplier == "2": multiplier = "hotness"
    else: multiplier = None
    if choice_menu == "1": # process all articles
        connection = sqlite3.connect("articles.sqlite")
        cursor = connection.cursor()
        if multiplier: data_articles = cursor.execute("SELECT title, label, lead, content, {} FROM Articles".format(multiplier))
        else: data_articles = cursor.execute("SELECT title, label, lead, content FROM Articles")
    elif choice_menu == "2": # process articles from a given time range
        while True:
            try:
                begin_str = input("Enter a valid start date in YYYY-MM-DD format: ")
                assert re.search("\d{4}-\d{2}-\d{2}", begin_str)
                begin = [int(d) for d in begin_str.split("-")]
                begin_date = date(begin[0], begin[1], begin[2])
                begin_datetime = datetime(begin[0], begin[1], begin[2])
                break
            except AssertionError:
                print("Date not in required format. Enter a date in YYYY-MM-DD format.")
            except ValueError:
                print("Date not valid. Enter a valid date.")
        while True:
            try:
                end_str = input("Enter a valid end date in YYYY-MM-DD format (end >= begin): ")
                assert re.search("\d{4}-\d{2}-\d{2}", end_str)
                end = [int(d) for d in end_str.split("-")]
                end_date = date(end[0], end[1], end[2])
                end_datetime = datetime(end[0], end[1], end[2])
                if int((end_datetime - begin_datetime).total_seconds()) < 0: raise DateError
                break
            except AssertionError:
                print("Date not in required format. Enter a date in YYYY-MM-DD format.")
            except ValueError:
                print("Date not valid. Enter a valid date.")
            except DateError:
                print("End date before start date. Enter valid end date.")
        connection = sqlite3.connect("articles.sqlite")
        cursor = connection.cursor()
        if multiplier: data_articles = cursor.execute("SELECT title, label, lead, content, {} FROM Articles WHERE time BETWEEN ? AND ?"
                                                      .format(multiplier), (begin_str, end_str)).fetchall()
        else: data_articles = cursor.execute("SELECT title, label, lead, content FROM Articles WHERE time BETWEEN ? AND ?",
                                             (begin_str, end_str)).fetchall()
    elif choice_menu == "3": # process articles with a custom WHERE clause for articles
        where = input("Enter a valid SQLite query WHERE clause for articles: ... WHERE ")
        connection = sqlite3.connect("articles.sqlite")
        cursor = connection.cursor()
        if multiplier: data_articles = cursor.execute("SELECT title, label, lead, content, {} FROM Articles WHERE ".format(multiplier) + where).fetchall()
        else: data_articles = cursor.execute("SELECT title, label, lead, content FROM Articles WHERE " + where).fetchall()
    else: # process articles with a custom WHERE clause for comments
        where = input("Enter a valid SQLite query WHERE clause for comments: ... WHERE ")
        connection = sqlite3.connect("articles.sqlite")
        cursor = connection.cursor()
        if multiplier: data_articles = cursor.execute("SELECT Comments.text, Articles.{} FROM Comments JOIN Articles ON Comments.id_article = Articles.idnum WHERE ".format(multiplier) + where).fetchall()
        else: data_articles = cursor.execute("SELECT Comments.text FROM Comments WHERE ".format(multiplier) + where).fetchall()
start = t()
frequencies = dict()
stopwords1 = ('a','ali','b','bi','bil','bila','bile','bili','bilo','biti','blizu','bo','bodo','bojo','bolj','bom',
              'bomo','boste','bova','boš','brez','c','cel','cela','celi','celo','d','da','datum','deset','deseta',
              'deseti','deseto','devet','deveta','deveti','deveto','do','dokler','dol','dolg','dolga','dolgi','dovolj',
              'drug','druga','drugi','drugo','dva','dve','e','eden','en','ena','ene','eni','enkrat','eno','etc.','f',
              'foto','g','g.','ga','ga.','gor','h','i','idr.','ii','iii','in','iv','ix','iz','j','jaz','je','ji','jih',
              'jim','jo','jutri','k','kadar','kadarkoli','kaj','kajti','kako','kakor','kakorkoli','kakršen',
              'kakršenkoli','kakršnega','kakršnegakoli','kakršnemu','kakršnemukoli','kakršnim','kakršnimkoli','kakšen',
              'kakšenkoli','kakšna','kakšnakoli','kakšne','kakšnega','kakšnegakoli','kakšnekoli','kakšnem',
              'kakšnemkoli','kakšnemu','kakšnemukoli','kakšni','kakšnih','kakšnihkoli','kakšnikoli','kakšnim',
              'kakšnimkoli','kakšno','kakšnokoli','kamor','kamorkoli','kar','karkoli','katera','katerakoli','katere',
              'katerega','kateregakoli','katerekoli','kateremu','kateremukoli','kateri','katerikoli','katerim',
              'katerimkoli','katero','katerokoli','kdaj','kdajkoli','kdo','kdor','kdorkoli','ker','ki','kje','kjer',
              'kjerkoli','ko','koder','koderkoli','koga','kogar','kogarkoli','koli','komu','komur','komurkoli','kot',
              'l','le','m','malce','malo','manj','me','med','medtem','mene','mi','midva','midve','mnogo','moj','moja',
              'moje','mora','morajo','moram','moramo','morate','moraš','morem','mu','n','na','nad','naj','najina',
              'najino','najmanj','naju','največ','nam','nas','nato','nazaj','naš','naša','naše','ne','nek','neka',
              'nekaj','nekatere','nekateri','nekatero','nekdo','neke','nekega','neki','nekje','neko','nekoga','nekoč',
              'ni','nikamor','nikdar','nikjer','nikoli','nič','nje','njega','njegov','njegova','njegovo','njej','njemu',
              'njen','njena','njeno','nji','njih','njihov','njihova','njihovo','njiju','njim','njo','njun','njuna',
              'njuno','no','nocoj','npr.','o','ob','oba','obe','oboje','od','okoli','on','onadva','one','oni','onidve',
              'osem','osma','osmi','osmo','oz.','p','pa','pet','peta','peti','peto','po','pod','pogosto','poleg','poln',
              'polna','polni','polno','ponavadi','ponovno','potem','povsod','prbl.','precej','pred','prej','preko',
              'pri','pribl.','približno','prva','prvi','prvo','r','ravno','redko','res','reč','s','saj','sam','sama',
              'same','sami','samo','se','sebe','sebi','sedaj','sedem','sedma','sedmi','sedmo','sem','seveda','si',
              'sicer','skoraj','skozi','smo','so','spet','sta','ste','sva','t','ta','tak','taka','take','taki','tako',
              'takoj','tam','te','tebe','tebi','tega','tem','ter','ti','tista','tiste','tisti','tisto','tj.','tja','to',
              'toda','tretja','tretje','tretji','tri','tu','tudi','tukaj','tvoj','tvoja','tvoje','u','v','vaju','vam',
              'vas','vaš','vaša','vaše','ve','vedno','vendar','ves','več','vi','vidva','vii','viii','vsa','vsaj','vsak',
              'vsaka','vsakdo','vsake','vsaki','vsakomur','vse','vsega','vsi','vso','včasih','včeraj','x','z','za',
              'zadaj','zadnji','zakaj','zaradi','zato','zdaj','zelo','zunaj','č','če','čegar','čegarkoli','čemur',
              'čemurkoli','česar','česarkoli','često','četrta','četrti','četrto','čez','čigar','čigarkoli','čigav','š',
              'še','šest','šesta','šesti','šesto','štiri','ž','že')
stopwords2 = ('0','1','2','3','4','5','6','7','8','9',':','a','ali','apr','april','aprila','avg','avgust','b','bi',
              'bil','bila','bile','bili','bilo','biti','blizu','bo','bodo','bojo','bolj','bom','bomo','bosta','boste',
              'bova','boš','brez','c','cel','cela','celi','celo','d','da','daleč','dalje','dan','danes','datum','dec',
              'december','del','dela','deset','deseta','deseti','deseto','devet','deveta','deveti','deveto','dnevi',
              'dni','do','dober','dobra','dobri','dobro','dodaten','dogodku','dokler','dokončna','dol','dolg','dolga',
              'dolgi','doo','dopolnil','dovolj','drug','druga','drugi','drugih','drugo','družbi','država','državni',
              'ds','dva','dve','dveh','e','eden','en','ena','ene','enega','eni','enkrat','eno','etc.','evrov','f',
              'false','feb','februar','function','g','g.','ga','ga.','glede','gor','gospa','gospod','gre','h','halo',
              'hitreje','i','idr.','if','ih','ii','iii','il','ima','imajo','imata','in','iv','ix','iz','izbora',
              'izboru','izjemen','j','jan','januar','jaz','je','ji','jih','jim','jo','js','jul','julij','jun','junij',
              'junija','jutri','k','kadarkoli','kaj','kajti','kako','kakor','kakovosti','kakšne','kamor','kamorkoli',
              'kar','karkoli','kategorija','kateri','katerikoli','katero','kdaj','kdo','kdorkoli','ker','ki','kje',
              'kjer','kjerkoli','klikov','ko','koder','koderkoli','koga','kombinacija','komentarjev','komu','konec',
              'kot','kratek','kratka','kratke','kratki','l','lahka','lahke','lahki','lahko','lani','le','lep','lepa',
              'lepe','lepi','lepo','let','leta','letih','letno','leto','letos','letu','linija','ljubljani','ljubljano',
              'ljudi','m','maj','maja','majhen','majhna','majhni','malce','malo','manj','mar','marca','marec','me',
              'med','medtem','meje','mene','mesec','mestu','mi','midva','midve','milijona','mnogo','mo','mogoče','moj',
              'moja','moje','mora','morajo','moram','moramo','morate','moraš','morda','more','morem','moremo','mu','n',
              'na','nad','naj','najbolj','najboljša','najdisi','najina','najino','najmanj','najpogosteje','naju',
              'najugodnejši','največ','največkrat','nam','namreč','narediti','narobe','narod','nas','nastop',
              'nastopila','nato','nazaj','način','naš','naša','naše','ne','nedavno','nedelja','nek','neka','nekaj',
              'nekatere','nekateri','nekatero','nekdanji','nekdo','neke','nekega','neki','nekje','neko','nekoga',
              'nekoč','net','ni','nikamor','nikdar','nikjer','nikoli','nima','nista','niste','nič','nje','njega',
              'njegov','njegova','njegovo','njej','njemu','njen','njena','njeno','nji','njih','njihov','njihova',
              'njihovo','njiju','njim','njo','njun','njuna','njuno','no','nocoj','nov','nova','nove','novega',
              'november','novi','novice','novih','novim','novimi','novo','npr.','o','ob','oba','obe','oboje','od',
              'odločitev','odprl','odprt','odprta','odprti','ogo','okoli','okt','oktober','on','onadva','one','oni',
              'onidve','or','osem','osma','osmi','osmo','oz.','oziroma','p','pa','pač','pet','peta','petek','peti',
              'peto','planet','po','pod','pogosto','pokala','poleg','poln','polna','polni','polno','ponavadi',
              'ponedeljek','ponovno','ponuja','potem','povsod','pozdravljen','pozdravljeni','počasi','prav','prava',
              'prave','pravi','pravijo','pravimi','pravo','prazen','prazna','prazno','prbl.','precej','pred',
              'predstavili','predvsem','prehodih','prej','prek','preko','premagan','pri','pribl.','približek',
              'približno','pridete','prikaže','prilo','priložnost','primer','primera','pripravljen','pripravljena',
              'pripravljeni','proti','prva','prvi','prvič','prvo','r','ra','rada','ravno','razkrivamo','redko','res',
              'reč','rešil','s','saj','sam','sama','same','sami','samo','se','sebe','sebi','sedaj','sedem','sedma',
              'sedmi','sedmo','sem','sep','september','seveda','seštevek','si','sicer','siolnet','skoraj','skozi',
              'skupnega','skupni','slab','slovenija','slovenije','sloveniji','slovenijo','slovenka','slovenska',
              'slovenske','slovenskem','slovenski','slovenskih','smo','so','sobota','soboto','spet','spletu','sprejela',
              'sprejet','sprejeti','sreda','srednja','srednji','sredo','sta','ste','storitve','stran','stvar','sva',
              'svet','svetu','svoj','svoje','svojem','svojo','t','ta','tak','taka','take','taki','tako','takoj','tam',
              'te','tebe','tebi','teden','tedna','tega','tekmi','tem','ter','termometer','težak','težka','težki',
              'težko','ti','tisoč','tista','tiste','tisti','tisto','tj.','tja','to','toda','tokrat','torek','tr',
              'treba','treh','trenutno','tretja','tretje','tretji','tri','true','tu','tudi','tukaj','tvoj','tvoja',
              'tvoje','u','udari','udarila','ujemata','upreti','uredi','v','vaju','vam','var','vas','vaš','vaša','vaše',
              'vašem','ve','vedeti','vedno','velik','velika','veliki','veliko','vendar','ves','več','večji','vi',
              'video','vidva','vii','viii','visok','visoka','visoke','visoki','vprašanje','vrača','vroč','vroča','vsa',
              'vsaj','vsak','vsaka','vsakdo','vsake','vsakem','vsaki','vsakomur','vse','vsega','vseh','vsi','vso',
              'včasih','včeraj','x','z','za','zadaj','zadnji','zadnjih','zakaj','zaprta','zaprti','zaprto','zaradi',
              'zato','zda','zdaj','združuje','zelo','zgodaj','zgolj','zna','znan','znova','zunaj','č','čas','če',
              'čeprav','često','četrta','četrtek','četrti','četrto','čez','čigav','čim','članek','š','še','šest',
              'šesta','šesti','šesto','števila','štiri','ž','že')
counter = 0
text = ""
for article in data_articles:
    if multiplier: multiplier_from_article = int(article[-1])
    else: multiplier_from_article = 1
    if choice_menu == "4":  words = word_tokenize(article[0].lower(), language="slovene")
    else: words = word_tokenize(" ".join(article[:-1]).lower(), language="slovene")
    text += " ".join(words) + " "
    for word in words:
        if word.isalnum() and not binarySearch(stopwords2, word): frequencies[word] = frequencies.get(word, 0) + multiplier_from_article
    counter += 1
if choice_wordcloud == "1":
    wordcloud = WordCloud(background_color="white", width=1600, height=1000, stopwords=stopwords2).generate(text)
    plt.figure(figsize=(16,10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout(pad=0)
    try: plt.savefig("wordcloud_from_{}_to_{}.jpg".format(begin_str, end_str))
    except NameError:
        if choice_menu == "1": plt.savefig("wordcloud.jpg")
        elif choice_menu == "4": plt.savefig("wordcloud_comments.jpg")
        else: plt.savefig("wordcloud_custom.jpg")
print()
for key, value in Counter(frequencies).most_common(10):
    print(value, key)
try: fh = open("most_freq_words_from_{}_to_{}.txt".format(begin_str, end_str), "w")
except NameError:
    if choice_menu == "1": fh = open("most_freq_words.txt", "w")
    elif choice_menu == "4": fh = open("most_freq_words_comments.txt", "w")
    else: fh = open("most_freq_words_custom.txt", "w")
for i in range(500):
    try: fh.write(Counter(frequencies).most_common()[i][0] + "\n")
    except IndexError: break
fh.close()
connection.close()
try: print("\nMost frequent words saved to most_freq_words_from_{}_to_{}.txt".format(begin_str, end_str))
except NameError:
    if choice_menu == "1": print("\nMost frequent words saved to most_freq_words.txt")
    elif choice_menu == "4": print("\nMost frequent words saved to most_freq_words_comments.txt")
    else: print("\nMost frequent words saved to most_freq_words_custom.txt")
if choice_wordcloud == "1":
    try: print("Word cloud image for selection saved as wordcloud_from_{}_to_{}.jpg".format(begin_str, end_str))
    except NameError:
        if choice_menu == "1": print("Word cloud image for selection saved as wordcloud.jpg")
        elif choice_menu == "4": print("Word cloud image for selection saved as wordcloud_comments.jpg")
        else: print("Word cloud image for selection saved as wordcloud_custom.jpg")
print("\n%d articles processed. Finished in %s seconds." % (counter, "{0:.3f}".format(t() - start)))