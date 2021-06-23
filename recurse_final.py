"""MODULE METER
===============
This module scans poems and guesses their meter.

Functions
---------
clean_poem(poem) : return poem without dashes
clean(word) : return word without punctuation, turn '&' to 'and'

preliminary_syllable_count_word() : Return number of vowels & vowel clusters.
adjustment_for_two_syll_clusters(word) : Return number of 2-syll clusters.
final_silent_e(word) : Return whether word's final e is likely silent.
other_silent_e(word) : Return whether other e's are likely silent (limited).
syllables(word) : Guess syllable count of word not in database using above fns.
get_syllable_count(word) : Get word's syll count from database or syllables(word).
get_syllables_per_line(poem) : Get list of syllable lengths of poem's lines.

calculate_probable_stress_ratio(word) : Guess unknown word's stress ratios based on averages from db.
get_stats(word) : Return ratio to calculate scansion.
poem_stats(poem) : Use get_stats on whole poem and return nested list.

house_robber_scan(poem) : Scan with solution to house robber problem
simple_scan(poem) : Scan based on ratios with no comparisons. (So far, useless)
house_robber_scan_weighted(poem) : Scan with house robber solution weighted toward 3-syll feet.
trochiamb_scan(poem) : Scan by stressing top half of stress ratios (Helps check other scansions)
anadactyl_scan() : Scan by stressing top third of stress ratios (Ditto)

average_foot_length(scansion_line) : Get stress count / syllable count
average_foot_length_poem(poem) : Get measures of ctrl tendency for diff scansions for foot length
foot_length_metric(poem) : Return whether median house_robber foot length <= 2 (2-syll feet)
scan_with_most_regular_average_foot_length(poem) : Return whether house robber or weighted house robber gives more regular foot lengths
trochiamb_correspondence(poem) : Get frequency of correspondence of house robber to trochiamb
anadactyl_correspondence(poem) : Get frequency of correspondence of weighted house robber to anadactyl
correspondence_metric(poem) : Return whether trochiamb correspondence or anadactyl correspondence greater

gather_data_from_known_poems_bayesian_single() : gather data for analysis using Bayes' theorem on single metrics
gather_data_from_known_poems_bayesian_full() : gather data for analysis using Bayes' theorem on combined metrics
bayesian(is_trochiamb, measure, data) : find probability poem has mostly 2-syll or 3-syll feet with one metric
bayesian_all(abbrev, data) : find probability poem has mostly 2-syll or 3-syll feet with all metrics
bayesian_count(abbrev, data) : find probability poem has mostly 2-syll or 3-syll feet with all metrics disregarding order
judge_accuracy() : find how often each metric gives correct results on sample data...rough estimate
testing_with_bayesian : see which metrics are best for what using Bayesian analysis

first_syllable_stressed(scansion) : Return whether first syll of each line is more often stressed
word_frequency(text, default_stopwords=DEFAULT_STOPWORDS, added_stopwords=[]) : find frequency of non-stopwords

guess_scansion(poem) : Return meter, scansion, and rough certainty of choice
format_scansion_for_console(poem, scansion) : Intersperse scansion and words to print
open_poem_file(filepath) : open given filename/path and read into string
"""


import re
import sqlite3
import math
import statistics
from copy import copy

import recurse_app_data

STRESSED = "/"
UNSTRESSED = "u"

# http://xpo6.com/list-of-english-stop-words/
DEFAULT_STOPWORDS = ["a", "about", "above", "across", "after", "afterwards", "again", "against", "all", "almost", "alone", "along", "already", "also","although","always","am","among", "amongst", "amoungst", "amount",  "an", "and", "another", "any","anyhow","anyone","anything","anyway", "anywhere", "are", "around", "as",  "at", "back","be","became", "because","become","becomes", "becoming", "been", "before", "beforehand", "behind", "being", "below", "beside", "besides", "between", "beyond", "bill", "both", "bottom","but", "by", "call", "can", "cannot", "cant", "co", "con", "could", "couldnt", "cry", "de", "describe", "detail", "do", "done", "down", "due", "during", "each", "eg", "eight", "either", "eleven","else", "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone", "everything", "everywhere", "except", "few", "fifteen", "fifty", "fill", "find", "first", "five", "for", "former", "formerly", "forty", "found", "four", "from", "front", "full", "further", "get", "give", "go", "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his", "how", "however", "hundred", "ie", "if", "in", "inc", "indeed", "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd", "made", "many", "may", "me", "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly", "move", "much", "must", "my", "myself", "name", "namely", "neither", "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own","part", "per", "perhaps", "please", "put", "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems", "serious", "several", "she", "should", "show", "side", "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone", "something", "sometime", "sometimes", "somewhere", "still", "such", "system", "take", "ten", "than", "that", "the", "their", "them", "themselves", "then", "thence", "there", "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they", "thick", "thin", "third", "this", "those", "though", "three", "through", "throughout", "thru", "thus", "to", "together", "too", "top", "toward", "towards", "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us", "very", "via", "was", "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever", "whole", "whom", "whose", "why", "will", "with", "within", "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves", "the"]

# The two constants below are used to "clean" poems (remove non-alphabetic characters, mostly)

# Only the characters listed in the following regular expression will be allowed (alphabetic characters and single hyphens). The e with the accute accent is the only letter with a diacritic mark I have encountered in Palgrave's Golden Treasury, the public-domain source of most of the poems I have been analyzing. If I run into, for example, ï as in naïve, or e with a grave accent, in that source or another, I will have to expand this regular expression and add those characters to the syllable counting regexes.
DISALLOWED = re.compile("[^-A-ZÉa-zé]")

# While single hyphens are allowed (and words containing them will get their own entries in the database in the larger app), double hyphens, n-dashes, and m-dashes, whether surrounded by spaces or not, will be removed.
DASH = re.compile(" *-- *| *– *| *— *")

def clean_poem(poem):
    """Return poem replacing dashes with spaces"""
    dashless = re.sub(DASH, " ", poem)
    # this once contained another variable to remove slashes and replace them with spaces, on the theory that some poem somewhere probably uses slashes in the usual way (as in the sentence "I am allergic to cats/dogs/grasses/whatever"), but a friend pointed out that slashes are much *likelier* to be used to represent line breaks; and in some modern poetry I have seen them used even in printed poems; I do not understand this last device well enough to know how to account for it in my poetry app, so for the moment I am not dealing with dashes in poetry lines and assuming (perhaps unwisely) that poems will be input with actual newlines rather than slashes.
    return dashless

def clean(word):
    """Return word lowercase and without nonalphabetic characters other than hyphens, replacing ampersands with ands"""
    wo = word.replace("&", "and")
    w = re.sub(DISALLOWED, "", wo)
    return w.lower()

#This second set of functions exists to count syllables programmatically -- it is a significant improvement over the open-source app that inspired it (Michael Holtzscher's SyllaPy, at https://github.com/mholtzscher/syllapy), but it is still, naturally, quite inexact (especially regarding silent e's in the middle of words). In the poetry app I linked in my application (https://github.com/Hathaway2010/poetry-react), it serves as a fallback for words not found in the database, which contains syllabification/stress-pattern information provided both by a dictionary and by users (at this point, I am the only user), but I thought it of enough interest to include it here.

def preliminary_syllable_count(word):
    """Count clusters of 1 or more vowels (each likely a syllable)"""
    vowels_or_vowel_clusters = re.findall("[AEÉIOUaeéiouy]+", word)
    return len(vowels_or_vowel_clusters)

def adjustment_for_two_syll_clusters(word):
    """Count clusters of vowels likely to have 2 syllables, not 1"""
    # This is massive and not intuitive. Examples of what it's doing can be found in tests/test_parse.py
    two_syllable_clusters = re.findall("[aiouy]é|ao|eo[^u]|ia[^n]|[^ct]ian|iet|io[^nu]|[^c]iu|[^gq]ua|[^gq]ue[lt]|[^q]uo|[aeiouy]ing|[aeiou]y[aiou]", word) # exceptions: Preus, Aida, poet, luau)
    return len(two_syllable_clusters)

def silent_final_e(word):
    """Return true if there is likely a silent final e"""
    # e is usually silent at the ends of word
    # but there are exceptions like "cable,"
    # "cadre," and "untrue"
    audible_final_e = re.compile('[^aeiouylrw]le$|[^aeiouywr]re$|[aeioy]e|[^g]ue')
    if word[-1] == "e" and not audible_final_e.search(word):
        return True
    return False

def other_silent_e(word):
    """Return true if other 'e's near end are likely silent"""
    # final -ed or -es unlikely to represent its own syllable
    silent_final_ed_es = re.compile("[^aeiouydlrt]ed$|[^aeiouycghjlrsxz]es$|thes$|[aeiouylrw]led$|[aeiouylrw]les$|[aeiouyrw]res$|[aeiouyrw]red$")
    # e in the middle unlikely to represent a syllable
    # as in 'lonely' or 'surely'
    consonant_e_ly = re.compile("[^aeiouy]ely$")
    # If I find ways to identify other silent 'e's in words,
    # like the 'e' in 'sometimes' or the first in 'nonetheless'
    # this function may be expanded
    if silent_final_ed_es.search(word) or consonant_e_ly.search(word):
        return True
    return False

def syllables(word):
    """Guess syllable count of word not in database.

    Parameters
    ----------
    word : str
        word not found in database
    
    Returns
    -------
    count : int
        estimated number of syllables
    
    See also
    --------
    tests/test_scan.py to clarify regular expressions
    """   
    cleaned_word = clean(word)
    compound = cleaned_word.split("-")
    total_count = 0
    for w in compound:
        if len(w) == 0:
            return 0
        # get preliminary count by counting vowels or clusters thereof
        count = preliminary_syllable_count(w)
        # increment count for all vowel clusters likely to be 2 syllables
        count += adjustment_for_two_syll_clusters(w)
        # subtract 1 for every likely silent e
        if silent_final_e(w):
            count -= 1
        if other_silent_e(w):
            count -= 1
            # words have at least one syllable
        if count <= 0:
            count = 1
        total_count += count
    return total_count

def get_syllable_count(word):
    """Gets word's syllable count from database if it's there or guesses it programmatically"""
    w = clean(word)
    conn = sqlite3.connect("poetrylite.db")
    c = conn.cursor()
    count = c.execute("SELECT syllables FROM stress_ratios WHERE word = :word", {"word": w}).fetchone()
    if count:
        return count[0]
    else:
        return syllables(word)

def get_syllables_per_line(poem):
    """Get list of syllable lengths of lines in poem"""
    p = clean_poem(poem)
    lines = p.splitlines()
    syllables_per_line = [sum(get_syllable_count(word) for word in line.split()) for line in lines if line]
    return syllables_per_line



# The functions below exist to find scansions of poems based on the contents of poetrylite.db; this database contains scansion data, some from dictionaries, some of which I've collected, for the 1000 most common words in the English langauge.

def calculate_probable_stress_ratio(word):
    """Calculate probable stress ratio for each syllable of a word not in the database."""
    conn = sqlite3.connect("poetrylite.db")
    c = conn.cursor()
    syllCount = syllables(word)
    # 4 is the max syllable count for the words in the db
    count_for_avg = min(syllCount, 4)
    ratio_list = []
    for i in range(syllCount):
        if i < 4:
            avg = c.execute(f"SELECT AVG(syll{i + 1}) FROM stress_ratios WHERE syllables = :syllables", {"syllables": count_for_avg})
            average = avg.fetchone()[0]
            try:
                ratio_list.append(round(average, 4))
            except TypeError:
                print(word, syllCount, count_for_avg, ": problems here")
        else:
            # Worth finding probability later syllables are stressed based on full db?
            ratio_list.append(0.3333)
    return ratio_list 

def get_stats(word):
    """Get stress statistics of a word in the db/mean stress statistics for a word of that length"""
    conn = sqlite3.connect("poetrylite.db")
    c = conn.cursor()
    ratios = c.execute("SELECT * FROM stress_ratios WHERE word = :word", {"word": word})
    w = ratios.fetchone()
    if w:
        ratio_list = []
        for syllable in range(w[2]):
            ratio_list.append(w[syllable + 3])
        c.close()
        return ratio_list
    c.close()
    return calculate_probable_stress_ratio(word)

def poem_stats(poem):
    """Find stress ratio for each word in a poem.

    Parameters
    ----------
    poem : str
        poem to scan
   
    Returns
    -------
    stress_list : list
        list of lists of stress ratios
    """
    # split poem into lines
    cleaned_poem = clean_poem(poem)
    lines = cleaned_poem.splitlines()
    poem_list = []
    # for each line get the list of stress probabilities (stressed / unstressed)
    # for each word and extend stress list with that sublist; for spaces, append a space
    for line in lines:
        words = line.split()
        word_list = []
        for word in words:
            # get version of word without non-alphabetic characters and lowercase
            w = clean(word)
            if w:
                stress = get_stats(w)
                word_list.extend(stress)
                word_list.append(" ")
        poem_list.append(word_list)
    return poem_list

# These are some scansion algorithms; house_robber_scan_weighted is designed to work better for three-syllable feet (though it is new, and I suspect the "weighting" process requires more thought), house_robber_scan for two-syllable feet. None of these algorithms work as well with the poetrylite database, since it contains only the 1000 most common words in English, as they do with the 100,000+ - entry database I have been using for the web app, but I hope I can keep refining.

def house_robber_scan(poem):
    """Scan poem by finding max sum of ratios with no adjacent stresses
    
    Parameters
    ----------
    poem : str
        poem to scan
    
    Returns
    -------
    scansion : str
        scansion with lines separated by newlines, words by spaces        
    """
    # inspired by https://leetcode.com/problems/house-robber/discuss/156523/From-good-to-great.-How-to-approach-most-of-DP-problems
    # get stress pattern of poem
    stress_list = poem_stats(poem)
    poem_scansion = []
    for line in stress_list:
        # remove spaces & add each value to a tuple with its index as the second value
        spaceless_line = []
        for i, value in enumerate(line):
            if value != " ":
                spaceless_line.append((value, i))
        # initialize two lists to represent potential stress patterns for the lines
        prev1 = []
        prev2 = []
        # iterate through spaceless line so constructed
        for pair in spaceless_line:
            tmp = copy(prev1)
            # https://stackoverflow.com/questions/25047561/finding-a-sum-in-nested-list-using-a-lambda-function
            # if the sum of stress values contained in prev1 is less than the sum
            # of stress values in prev2 + the current stress value
            # make prev1 a copy of prev2
            if sum(p[0] for p in prev1) <= sum(p[0] for p in prev2) + pair[0]:
                prev2.append(pair)
                prev1 = copy(prev2)
            # either way, make the previous prev1 prev2
            prev2 = copy(tmp)
        # iterate through original line, adding to a scansion
        line_scansion = ""
        for i, value in enumerate(line):
            # carry spaces over into the scansion untouched
            if value == " ":
                line_scansion += value
            # otherwise, if a given value is an index included in prev1,
            # which is the "winner" for highest values
            # make it stressed, and if it is not, make it unstressed
            elif [pair for pair in prev1 if pair[1] == i]:
                line_scansion += STRESSED
            else:
                line_scansion += UNSTRESSED
        poem_scansion.append(line_scansion)
    return "\n".join(poem_scansion)
    

def simple_scan(poem):
    """Scan poem using ratios but not comparing them
    
    Parameters
    ----------
    poem : str
        poem to scan
    
    Returns
    -------
    scansion : str
        scansion with lines separated by newlines, words by spaces
    """
    stats = poem_stats(poem)
    poem_scansion = []
    for line in stats:
        line_scansion = ""
        if line:
            for value in line:
                if value == " ":
                    line_scansion += value
                elif value > 1:
                    line_scansion += STRESSED
                else:
                    line_scansion += UNSTRESSED
        poem_scansion.append(line_scansion)
    return "\n".join(poem_scansion)

def house_robber_scan_weighted(poem):
    """Scan poem by finding max sum of weighted ratios with no adjacent stresses
    
    Parameters
    ----------
    poem : str
        poem to scan
    
    Returns
    -------
    scansion : str
        scansion with lines separated by newlines, words by spaces        
    """
    # get stress pattern of poem
    stress_list = poem_stats(poem)
    poem_scansion = []
    for line in stress_list:
        # remove spaces and replace question marks with a guess of 0.3
        # add each value to a tuple containing its index as the second value
        spaceless_line = []
        for i, value in enumerate(line):
            if value != " ":
                if value == "?":
                    spaceless_line.append([0.3, i])
                else:
                    spaceless_line.append([value, i])
        # initialize two lists to represent potential stress patterns for the lines
        prev1 = []
        prev2 = []
        # iterate through spaceless line so constructed
        for i, pair in enumerate(spaceless_line):
            tmp = copy(prev1)
            # https://stackoverflow.com/questions/25047561/finding-a-sum-in-nested-list-using-a-lambda-function
            # if the sum of stress values contained in prev1 is less than the sum
            # of stress values in prev2 + the current stress value
            # make prev1 a copy of prev2
            skip_num = 1
            if prev2:
                skip_num = i - spaceless_line.index(prev2[-1])
            if skip_num < 3:
                if sum(p[0] for p in prev1) <= sum(p[0] for p in prev2) + pair[0]:
                    prev2.append(pair)
                    prev1 = copy(prev2)
            else:
                if sum(p[0] for p in prev1) <= sum(p[0] for p in prev2) + pair[0] * 5:
                    pair[0] *= 5
                    prev2.append(pair)
                    prev1 = copy(prev2)
            # either way, make the previous prev1 prev2
            prev2 = copy(tmp)
        # iterate through original line, adding to a scansion
        line_scansion = ""
        for i, value in enumerate(line):
            # carry spaces over into the scansion untouched
            if value == " ":
                line_scansion += value
            # otherwise, if a given value is an index included in prev1,
            # which is the "winner" for highest values
            # make it stressed, and if it is not, make it unstressed
            elif [pair for pair in prev1 if pair[1] == i]:
                line_scansion += STRESSED
            else:
                line_scansion += UNSTRESSED
        poem_scansion.append(line_scansion)
    return "\n".join(poem_scansion)

# These two scansion algorithms are abominations as regards accurate scansion, but I am interested to compare each to its appropriate house robber scan, to see what I can learn about how poems wrench words from their usual stress patterns.
def trochiamb_scan(poem):
    """Scan a poem as if it has two-syllable feet.
    
    Parameters
    ----------
    poem : str
        poem to scan
    
    Returns
    -------
    scansion : str
        scansion with lines separated by newlines, words by spaces        
    """
    stress_list = poem_stats(poem)
    poem_scansion = []
    for line in stress_list:
        spaceless_line = []
        for i, value in enumerate(line):
            if value != " ":
                spaceless_line.append([value, i])
        length = len(spaceless_line)
        approx_stress_count = math.ceil(length / 2)
        spaceless_line.sort(key=lambda x: x[0], reverse=True)
        stresses = spaceless_line[: approx_stress_count]
        line_scansion = ""
        for i, value in enumerate(line):
            if value == " ":
                line_scansion += value
            elif [value, i] in stresses:
                line_scansion += STRESSED
            else:
                line_scansion += UNSTRESSED
        poem_scansion.append(line_scansion)
    return "\n".join(poem_scansion)

def anadactyl_scan(poem):
    """Scan a poem as if it has three-syllable feet.
    
    Parameters
    ----------
    poem : str
        poem to scan
    
    Returns
    -------
    scansion : str
        scansion with lines separated by newlines, words by spaces        
    """
    stress_list = poem_stats(poem)
    poem_scansion = []
    for line in stress_list:
        spaceless_line = []
        for i, value in enumerate(line):
            if value != " ":
                spaceless_line.append([value, i])
        length = len(spaceless_line)
        approx_stress_count = math.ceil(length / 3)
        spaceless_line.sort(key=lambda x: x[0], reverse=True)
        stresses = spaceless_line[: approx_stress_count]
        line_scansion = ""
        for i, value in enumerate(line):
            if value == " ":
                line_scansion += value
            elif [value, i] in stresses:
                line_scansion += STRESSED
            else:
                line_scansion += UNSTRESSED
        poem_scansion.append(line_scansion)
    return "\n".join(poem_scansion)

# The following functions are the newest part of this app, and they exist to evaluate scansion algorithms by comparing them to one another and collecting other data about them. I hope to be able to distinguish iambic/trochaic meters (meters with two-syllable feet) from anapestic/dactylic meters (meters with three-syllable feet), but this proves surprisingly difficult. I have never studied math or statistics formally beyond the high school level. The following, and the section after it, feels more like what happens when a child gets a new box of crayons than the work of an accomplished artist, but it *is* a lot of fun.
        
def average_foot_length(scansion_line):
    """Find mean foot length of a line in a scansion"""
    stress_count = scansion_line.count(STRESSED)
    syllable_count = stress_count + scansion_line.count(UNSTRESSED)
    return syllable_count / stress_count if stress_count > 0 else syllable_count

def average_foot_length_poem(poem):
    """Find measures of ctrl tendency for line's average foot length for each scansion"""
    SCANSION_ALGORITHMS = [
        ("simple", simple_scan),
        ("trochiamb", house_robber_scan),
        ("anadactyl", house_robber_scan_weighted)
    ]
    central_values = []
    for alg in SCANSION_ALGORITHMS:
        average_foot_lengths = []
        scansion = alg[1](poem)
        for line in scansion.splitlines():
            if line:
                average_foot_lengths.append(average_foot_length(line))
        # no longer using these other measures of central tendency but might at some point
        # mn = statistics.mean(average_foot_lengths)
        mdn = statistics.median(average_foot_lengths)
        # mde = statistics.mode(average_foot_lengths)
        central_values.append((alg[0], mdn))
    return central_values

def foot_length_metric(poem):
    """Guess poem's meter based on average foot length in house_robber_scan."""
    # I decided on the 2.0 cutoff because the iambic poems mostly had (surprise!) feet of 2 syllables, and even modestly more in the house_robber_scan (which favors two-syllable feet heavily) suggests anapestic meter
    if average_foot_length_poem(poem)[1][1] > 2.0:
        return "a"
    else:
        return "t"

def scan_with_most_regular_average_foot_length(poem):
    """Determine whether house_robber_scan (2-syll foot) or house_robber_scan_weighted (3-syll) produces most regular foot lengths."""
    SCANSION_ALGORITHMS = [
        ("trochiamb", house_robber_scan),
        ("anadactyl", house_robber_scan_weighted)
    ]
    variances = []
    for alg in SCANSION_ALGORITHMS:
        average_foot_lengths = []
        scansion = alg[1](poem)
        for line in scansion.splitlines():
            if line:
                average_foot_lengths.append(average_foot_length(line))
        v = statistics.pvariance(average_foot_lengths)
        variances.append((alg[0], v))
    variances = sorted(variances, key=lambda x: x[1])
    if variances[0] == variances[1]:
        return "equal"
    else:
        return variances[0][0]

def trochiamb_correspondence(poem):
    """Determine percentage of accents shared between house_robber_scan and trochiamb_scan, should correlate positively with many 2-syll feet"""
    hr = house_robber_scan(poem)
    t = trochiamb_scan(poem)
    corresCounter = 0
    charCounter = 0
    for i, char in enumerate(hr):
        if char == t[i] == STRESSED:
            corresCounter += 1
        if t[i] == STRESSED:
            charCounter += 1
    return corresCounter / charCounter

def anadactyl_correspondence(poem):
    """Determine percentage of accents shared between house_robber_scan_weighted and anadactyl_scan, should correlate positively with many 3-syll feet"""
    hrw = house_robber_scan_weighted(poem)
    a = anadactyl_scan(poem)
    corresCounter = 0
    charCounter = 0
    for i, char in enumerate(hrw):
        if char == a[i] == STRESSED:
            corresCounter += 1
        if a[i] == STRESSED:
            charCounter += 1
    return corresCounter / charCounter

def correspondence_metric(poem):
    tc = trochiamb_correspondence(poem)
    ac = anadactyl_correspondence(poem)
    if tc >= ac:
        return "t"
    else:
        return "a"

# The following few functions examine a number of poems in recurse_app_data.py to determine how helpful the different metrics are.

def gather_data_from_known_poems_bayesian_single():
    """Get dictionary of likelihood of three diff metrics to id 2-syll vs3-syll feet"""
    # recurse_app_data contains a variety of poems by me and others, in a variety of meters. I try various my three metrics on various my three scansions in an attempt to find a way to accurately identify patterns of two vs three-syllable feet.
    classified = recurse_app_data.CLASSIFIED
    all_data = {}
    total_length = 0
    for category in classified:
        regularity_t = 0
        correspondence_t = 0
        foot_length_t = 0
        for poem in classified[category]:
            most_regular = scan_with_most_regular_average_foot_length(poem)[0][0]
            correspondences = correspondence_metric(poem)
            median_foot_length = foot_length_metric(poem)
            if most_regular == "t":
                regularity_t += 1
            if correspondences == "t":
                correspondence_t += 1
            if median_foot_length == "t":
                foot_length_t += 1
        length = len(classified[category])
        total_length += length
        category_data = {
            "regularityt": regularity_t, 
            "regularitya": length - regularity_t, 
            "correspondencet": correspondence_t, 
            "correspondencea": length - correspondence_t,
            "foot_lengtht": foot_length_t,
            "foot_lengtha": length - foot_length_t,
            "length": length
            }
        all_data[category] = (category_data)
    return all_data, total_length

def gather_data_from_known_poems_bayesian_full():
    """Get dictionary of likelihood of three metrics taken together to id 2-syll vs 3-syll feet."""
    classified = recurse_app_data.CLASSIFIED
    all_data = {}
    total_length = 0
    for category in classified:
        category_dict = {
            "ttt": 0,
            "tta": 0,
            "tat": 0,
            "att": 0,
            "taa": 0,
            "ata": 0,
            "aat": 0,
            "aaa": 0,
            "length": len(classified[category])
        }
        for poem in classified[category]:
            most_regular = scan_with_most_regular_average_foot_length(poem)[0][0]
            tc = trochiamb_correspondence(poem)
            ac = anadactyl_correspondence(poem)
            correspondences = "t" if tc >= ac else "a"
            median_foot_length = "a" if average_foot_length_poem(poem)[1][1] > 2 else "t"
            category_dict[most_regular + correspondences + median_foot_length] += 1
        total_length += category_dict["length"]
        all_data[category] = category_dict
    return all_data, total_length

def bayesian(is_trochiamb, measure, data):
    """Should find probability that any poem has mostly 2- or 3- syllable feet based on result of single metric."""
    # P(A|B) = (P(B|A) * P(A)) / P(B)
    if measure not in ["regularity", "correspondence", "foot_length"]:
        raise Exception("Measure needs to be one of 'regularity', 'correspondence', or 'foot_length'")
    if is_trochiamb:
        to_look_up = measure + "t"
    else:
        to_look_up = measure + "a"
    results_dict = {}
    for category in data[0]:
        prob = ((data[0][category][to_look_up] / data[0][category]["length"]) * data[0][category]["length"] / data[1]) / (sum(data[0][cat][to_look_up] for cat in data[0]) / data[1] )
        results_dict[category] = prob
    return results_dict

def bayesian_all(abbrev, data):
    """Should find probability that any poem has mostly 2- or 3- syllable feet based on result of 3 metrics together."""
    # P(A|B) = (P(B|A) * P(A)) / P(B)
    results_dict = {}
    frequency_of_combintion = sum(data[0][cat][abbrev] for cat in data[0])
    if frequency_of_combintion != 0:
        for category in data[0]:
            prob = ((data[0][category][abbrev] / data[0][category]["length"]) * (data[0][category]["length"] / data[1])) / (sum(data[0][cat][abbrev] for cat in data[0]) / data[1])
            results_dict[category] = prob
        return results_dict
    else:
        raise Exception("We haven't seen this combination yet!")

def bayesian_count(abbrev, data):
    """Should find probability that any poem has mostly 2- or 3- syllable feet based on # of metrics that are 't'"""
    # P(A|B) = (P(B|A) * P(A)) / P(B)
    results_dict = {}
    count = abbrev.count('t')
    frequency_of_count = sum(data[0][cat][count] for cat in data[0])
    for category in data[0]:
        prob = ((data[0][category][count] / data[0][category]["length"]) * (data[0][category]["length"] / data[1])) / (frequency_of_count / data[1])
        results_dict[category] = prob
    return results_dict

def judge_accuracy():
    """Find out how many times each metric correspodns with my classification of my poems."""
    classified = recurse_app_data.CLASSIFIED
    accuracies = {"regularity": 0, "correspondence": 0, "foot_length": 0, "two_or_more": 0}
    for category in classified:
        print(category.upper())
        for poem in classified[category]:
            r = scan_with_most_regular_average_foot_length(poem)[0]
            c = correspondence_metric(poem)
            f = foot_length_metric(poem)
            abbrev = r + c + f
            print(abbrev)
            if category == "iambic/trochaic":
                if r == "t":
                    accuracies["regularity"] += 1
                if c == "t":
                    accuracies["correspondence"] += 1
                if f == "t":
                    accuracies["foot_length"] += 1
                if abbrev.count("t") >= 2:
                    accuracies["two_or_more"] += 1
            else:
                if r == "a":
                    accuracies["regularity"] += 1
                if c == "a":
                    accuracies["correspondence"] += 1
                if f == "a":
                    accuracies["foot_length"] += 1
                if abbrev.count("t") < 2:
                    accuracies["two_or_more"] += 1
    return accuracies                         
    
def testing_with_bayesian():
    """Test a few guesses about probability"""
    # When I change the poems included in recurse_app_data.py or the algorithms I use on them I will re-run the relevant functions, but said functions (gather_data_from_known_poems_bayesian_single and gather_data_from_known_poems_bayesian_full) are, to put it mildly time-consuming, so I am hard-coding their results in for these experiments.    
    data_full = ({'iambic/trochaic': {'ttt': 28, 'tta': 2, 'tat': 7, 'att': 1, 'taa': 1, 'ata': 1, 'aat': 0, 'aaa': 0, 'length': 40}, 'anapestic/dactylic': {'ttt': 2, 'tta': 0, 'tat': 1, 'att': 0, 'taa': 2, 'ata': 1, 'aat': 0, 'aaa': 6, 'length': 12}}, 52)
    # This (counted from data_full) represents the number of abbreviations with the listed # of t's
    data_count = ({"iambic/trochaic": {3: 21, 2: 10, 1: 3, 0: 0, "length": 34}, "anapestic/dactylic": {3: 1, 2: 2, 1: 2, 0: 6, "length": 11}}, 45)
    data = ({'iambic/trochaic': {'regularityt': 38, 'regularitya': 2, 'correspondencet': 32, 'correspondencea': 8, 'foot_lengtht': 36, 'foot_lengtha': 4, 'length': 40}, 'anapestic/dactylic': {'regularityt': 5, 'regularitya': 7, 'correspondencet': 3, 'correspondencea': 9, 'foot_lengtht': 3, 'foot_lengtha': 9, 'length': 12}}, 52)
    print("A foot length <= 2 is unlikely to deceive: it means trochees or iambs")
    print(bayesian(True, "foot_length", data))
    print("A regularity indicating anadactyl is fairly likely to be correct too")
    print(bayesian(False, "regularity", data))
    print("'aaa' is almost certain to by anapestic or dactylic")
    print(bayesian_all("aaa", data_full))
    print("'ttt' is very likely to be trochaic or iambic.")
    print(bayesian_all("ttt", data_full))
    print("Abbrev.count('t') == 2 gives likely iambic/trochaic.")
    print(bayesian_count('tta', data_count))
    print("and abbrev.count('a') == 2 gives, alas, likely iambic/trochaic too!")
    print(bayesian_count('taa', data_count))


# The following functions test other aspects of the poem that are easier to judge.

def first_syllable_stressed(scansion):
    """Distinguish between iambic and trochaic or anapestic and dactylic meters."""
    lines = scansion.splitlines()
    length = len(lines)
    stress_count = 0
    for line in lines:
        if line:
            idx = 0
            while line[idx] == " ":
                idx += 1
            if line[idx] == STRESSED:
                stress_count += 1
    ratio = stress_count / length
    # some exploration may be needed to find appropriate cutoffs, what constitutes an ambiguous situation, etc.
    return ratio > 0.5

def word_frequency(text, default_stopwords=DEFAULT_STOPWORDS, added_stopwords=[]):
    """Finds most frequently occurring non-stopwords in poem."""
    stopwords = default_stopwords + added_stopwords
    cleaned_text = clean_poem(text)
    words = [clean(word) for word in cleaned_text.split()]
    raw_dict = {}
    count_list = []
    word_count = len(words)
    for word in words:
        if word in raw_dict:
            raw_dict[word] += 1
        else:
            raw_dict[word] = 1
    for word in raw_dict:
        if word not in stopwords:
            count_list.append((word, raw_dict[word]))
    count_list = sorted(count_list, key=lambda word: word[1], reverse=True)
    return {"words and popularities excluding stopwords": count_list, "words and popularities including stopwords": raw_dict}

# The following functions "pull it all together"

def guess_info(poem):
    """Uses statistics gathered above to produce likely-best scansion, likely meter, and degree of certainty."""
    r = scan_with_most_regular_average_foot_length(poem)[0]
    c = correspondence_metric(poem)
    f = foot_length_metric(poem)
    abbrev = r + c + f
    foot_type = 0
    certainty = "low"
    if abbrev == "aaa":
        foot_type = "a"
        certainty = "high"
    elif abbrev == "ttt" or abbrev[2] == "t":
        foot_type = "t"
        certainty = "high"
    elif abbrev[0] == "a":
        foot_type = "a"
        certainty = "medium"
    else:
        foot_type = "t"
        certainty = "low"
    if foot_type == "a":
        scansion = house_robber_scan_weighted(poem)
    else:
        scansion = house_robber_scan(poem)
    if first_syllable_stressed(scansion):
        if foot_type == "t":
            meter = "trochaic"
        else:
            meter = "dactylic"
    else:
        if foot_type == "t":
            meter = "iambic"
        else:
            meter = "anapestic"
    return meter, certainty, scansion 

def format_scansion_for_console(poem, scansion):
    """Takes a scansion separated by spaces and newlines and interpolates the words of its poem"""
    poem_lines = clean_poem(poem).splitlines()
    poem_words = [[word for word in line.split()] for line in poem_lines]
    scansion_lines = scansion.splitlines()
    scansion_words = [[word for word in line.split()] for line in scansion_lines]
    if len(poem_lines) != len(scansion_lines):
        raise Exception("Poem and scansion do not match in line length.")
    display_list = []
    for i, line in enumerate(poem_words):
        line_string = ""
        if len(line) != len(scansion_words[i]):
            raise Exception(f"{line} and {scansion_words[i]} don't match in line {i}")
        for j, word in enumerate(line):
            line_string += f"{scansion_words[i][j]}({word}) "
        display_list.append(line_string)
    return "\n".join(display_list)

def open_poem_file(file_path):
    """Return single poem contained in file as string."""
    with open(file_path) as file:
        return file.read()


def main():

    print()
    print("Please give me the path to a plain text file")
    print("containing only the poem you're curious about.")
    print()
    print("Please leave out title, author, date, dedication, etc.")
    print()
    path = input("Path to file: ")
    while True:
        try:
            poem = open_poem_file(path)
            break
        except(FileNotFoundError):
            print("Sorry, I couldn't find that file.")
            path = input("Try again: ")
    info = guess_info(poem)
    frequent_words_no_stopwords = word_frequency(poem)["words and popularities excluding stopwords"]
    words_to_show = [word for word in frequent_words_no_stopwords if word[1] > 1]
    print("Here is my best guess at a scansion ('/' indicates stressed syllables, 'u' unstressed).")
    print(format_scansion_for_console(poem, info[2]))
    print()
    print(f"I would say with a {info[1]} degree of certainty that this poem is in {info[0]} meter")
    print()
    print("Here are the words that occur more than once in this poem, excluding stopwords:")
    for word in words_to_show:
        print(f"The poem contains {word[1]} of {word[0]}.")
    
main()