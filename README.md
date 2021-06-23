# Meter

## Introduction

This is a Python console app that makes use of the data I collected working on [poetry-scansion](https://github.com/Hathaway2010/poetry-scansion) and [poetry-react](https://github.com/Hathaway2010/poetry-react) (demos [here](https://poetry-scansion.repl.co) and [here](https://poetry-react.repl.co) respectively) to attempt to scan English-language poems and identify their meters. Provided with an English-language poem, it will print to the terminal its best guess at a scansion, its best guess at a meter, and how certain it is about the meter.

### For Recurse: Which Code Is Mine

This project uses various modules from Python's standard library (specifically, `sqlite3`, `re`, `math`, `statistics`, and `copy`) as well as a SQLite database. All of the code you actually see written in the documents is mine, but I did not reimplement the interface with SQLite that `sqlite3` provides (so the various occurrences of things like 

    conn = sqlite3.connect("poetrylite.db")
    c = conn.cursor()
    result = c.execute("SOME sqlite QUERY").fetchone()

are a result of my research on how to use the preexisting sqlite3 module (the queries themselves are my own, though they often involved re-Googling SQLite syntax). Likewise, functions like `math.ceil`, `re.compile`, and `statistics.pvariance` and `copy` are, unsurprisingly, not of my own devising.

However, the functions `house_robber_scan` and `house_robber_scan_weighted` took heavy inspiration (as cited below and in the code) from [a solution](https://leetcode.com/problems/house-robber/discuss/156523/From-good-to-great.-How-to-approach-most-of-DP-problems) to a coding challenge (I came across this challenge by coincidence and was tickled to notice that it was eerily similar to the problem of scanning poetry!). In addition, Michael Holtzscher's [SyllaPy](https://github.com/mholtzscher/syllapy) and his [blog post](https://mholtzscher.github.io/2018/05/29/syllables/) about it gave me a starting point for counting syllables programmatically in the function `syllables`.

## How to Use

To use this app, you need Python 3 and sqlite3 installed. You should also find some metrical poetry to scan! Put each poem in a separate plain text file, without title, author, dedication, etc -- just the text of the poem. (This app is, alas, in its current state of development, quite fussy about formatting; you will want to replace curly quotes with straight quotes and ellipses that are single characters with series of three separate periods; also, for other reasons, punctuation other than dashes or ampersands separated from words by spaces is likely to cause problems -- if this happens, just delete the spaces surrounding the punctuation in the text document, and you should be good to go.) Then, clone the repository, navigate on the command line to the recurse-0621 directory, and type `python recurse_final.py` (or possibly `python3 recurse_final.py`). You will be prompted for the path to one of these text files. Provide it, hit enter, and see what happens. 

## About the Automated Scansion Process

The app's scansion of a line of poetry depends most fundamentally upon the ratio between the number of times each syllable of each word has been marked (in a dictionary or by me, scanning poems for poetry-scansion) as stressed to the number of times that syllable has been marked as unstressed. All of my algorithms so far are based on calculations of this ratio. 

Originally, I collected data by scanning numerous poems and recording the results in a database that already had pronunciation data for multi-syllable words from *Webster's Unabridged Dictionary* from 1913, downloaded from Project Gutenberg and mined for the appropriate information. Collecting data was necessary because, first, this dictionary does not contain all words (especially plurals, different tenses, etc.) and, second and more important, entries for single-syllable words do provide any information about how they will be stressed in context, and I would guess that more than half of the words in any poem have only one syllable. 

For this project, I wrote `recurse_app_slim_db.py` to take data for the 1000 most commonly used words in English (word list from [this](https://gist.github.com/deekayen/4148741) GitHub gist from my 100,000+-entry original database; I may at some point want to find the 1000 most common words used in, say, Palgrave's Golden Treasury, the centuries-spanning anthology of poetry I used for poetry-react and poetry-scansion.) For the reason mentioned above (other conjugations/tenses/numbers of words are not included in this dictionary) it was necessary to devise a means of counting syllables programmatically. In this I was inspired by Michael Holtzscher's [syllapy](https://github.com/mholtzscher/syllapy), although I have added more sensitivity, most notably regarding silent -ed and -es, by using regular expressions.

The best algorithm I call the House Robber algorithm because it was strongly based on [this](https://leetcode.com/problems/house-robber/discuss/156523/From-good-to-great.-How-to-approach-most-of-DP-problems) solution to the House Robber problem on LeetCode. The algorithm finds the combination of "houses" (in this case, syllables) that gives it the maximum sum of loot (here, defined as the stressed / unstressed ratio) without skipping more than two syllables in a row or accenting two adjacent syllables. Now, my experimentation so far suggests, the algorithm usually gets only 0.2- 0.02 of the words wrong in poetry with mostly 2-syllable feet (iambic or trochaic poetry.)

For poems with mostly 3-syllable feet (anapestic or dactylic poems), I have tried reimplementing the House Robber solution with different weighting. This does slightly better than plain House Robber -- but I very much doubt that it is ideal, and will have to keep experimenting.

To experiment, I implemented a third algorithm, which I call Simple Scan: it guesses the stressed or unstressed status of a syllable based simply on the stressed/unstressed ratio, using no comparison. I hypothesize that this would do better for prose or verse that does not follow any particular metrical pattern. 

I also implemented two algorithms based on Simple Scan: Trochiamb Scan and Anadactyl Scan, in which I find the top half or third of the ratios respectively and interpret those syllables as stressed. Experience suggests these are mostly worthless as scansion algorithms, but they can be used to see whether House Robber or House Robber Weighted is a better fit (more on that later).

## About the Statistical Analysis

The statistical analysis, such as it is, is the newest part of this app, and is based on a combination of haphazard research, dim memory, intuition, and experimentation. What I have done 1) is almost certainly profoundly messy and inexpert, 2) mostly works, and 3) was enough fun that I find myself wanting to get into statistics.

Ultimately, I hope that my poetry analysis software will be able to identify a range of characteristics in poetry -- whether the poem hews to an established form (haiku, sonnet, Spenserian stanzas, etc.), whether a poem is metrical at all, whether a meter is accentual, syllabic, or accentual-syllabic, whether there are patterns in line lengths more complex than pure regularity (for a simple example, ballad meter typically involves quatrains with alternating lines of four and three stressed syllables.) 

What emerged from this analysis was a programmatic means of identifying the four most common accentual-syllabic meters in English poetry: iambic (each line has, approximately, the rhythm duh-DUH-duh-DUH), trochaic (DUH-duh), anapestic (duh-duh-DUH), and dactylic (DUH-duh-duh). The hardest part was distinguishing between meters with two-syllable feet (iambic/trochaic) and meters with three-syllable feet (anapestic/dactylic). 

`house_robber_scan` is heavily biased toward finding two-syllable feet (because a line of ratios like 3, 2, 2, 3, 2, 2 gives a higher sum for 3 + 2 + 3 than 3 + 3 even though the pattern is clearly otherwise). `house_robber_scan_weighted`, meanwhile, favors a slightly longer average foot.

I found three metrics for which of these two algorithms (and, thus, which foot length) was likely most accurate, which often yield different results, but which, taken together, allow educated guesses.

The most straightforward, perhaps, I refer to as `average_foot_length`, `foot_length`, or `f`: for each line, I divide the number of syllables by the number of stressed syllables found by `house_robber_scan` and take the median across lines. It turns out that poems with two-syllable feet often have a median of 2.0, very neatly! Because, of course, `house_robber_scan` favors two-syllable feet, its average scansion for poems with three-syllable feet does not even approach 3, but it does tend to be a bit higher than 2.0. (Patterns in average foot length with `simple_scan` and `house_robber_scan_weighted` seemed, upon perhaps insufficient examination, less informative, so I chose to focus on `house_robber_scan`).

Another measure (about equally helpful), which I refer to as `scan_with_most_regular_average_foot_length`, `regularity`, or `r`, goes a level up from average_foot_length: it measures the *regularity* of average foot length across lines, on the theory that an accurate scansion is likely to produce more regular foot lengths (assuming the poem has regular foot lengths!).

A third (somewhat less helpful but still gets it right ~80% of the time with the poems I've selected) measures the degree of correspondence between `house_robber_scan` of a poem and `trochiamb_scan` and compares it to the degree of correspondence between `house_robber_scan_weighted` and `anadactyl_scan`.

The file `recurse_app_data.py` contains a variety of public-domain poems in different meters, classified according to foot length (I found things much less confusing if I assumed a binary split between 3-syllable and 2-syllable feet and so, in my final version, included only those two categories, but I would like to be able to identify mixed feet as well)

## About the Poems

All of the poems in `recurse_app_data.py` come from William Braithwaite's 1913 *Anthology of Massachusetts Poets* from Project Gutenberg. 

## Future Directions
- I suspect I should do the House Robber scan on a logarithmic scale, albeit offset so that all numbers are positive. This is because at present differences among stress ratios greater than 1 will be weighted much more heavily than differences among stress ratios less than one. The magic of House Robber Scan depends on all numbers' being positive (so that no more than two syllables will ever be skipped).
- Regarding statistical analysis, I would like to be able to take into account gradations in my three metrics rather than creating a semi-arbitrary cutoff to divide results into groups. I would also like to assess these metrics against a larger and more diverse body of poetry. Eventually, I hope to study statistics so as to have a broader and better understanding of the tools at hand.
- While the House Robber algorithm has improved my app's scansion ability enormously, I look forward to experimenting with more possibilities. I might want to: take into account words' positions in their lines, their part of speech, the grammatical role they play, the total number of ratings the word has received instead of just the ratio of one stress pattern to another (so that a word that has a stress ratio of 1.123 that has been scanned 100 times might somehow be assigned more authority than a word that has been scanned 3 times to be stressed and thus has a stress ratio of 3)
- As I mentioned, I would like to start exploring line length (both in terms of numbers of syllables and numbers of stressed syllables) and determining whether verse is metrical at all. In addition, I hope eventually to start identifying devices such as rhyme, alliteration, and assonance, as well as the quirks of individual poets.
- Eventually, I hope to apply machine learning to these problems (scansion, identification of meter, determination of whether there is meter, etc.) 
 