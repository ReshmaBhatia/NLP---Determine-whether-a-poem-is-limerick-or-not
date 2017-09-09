#!/usr/bin/env python
import argparse
import sys
import codecs

if sys.version_info[0] == 2:
    from itertools import izip
else:
    izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit

# Use word_tokenize to split raw text into words
from string import punctuation

import nltk
from nltk.tokenize import word_tokenize

import string


scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
    if type(fh) is str:
        fh = open(fh, code)
    ret = gzip.open(fh.name, code if code.endswith("t") else code + "t") if fh.name.endswith(".gz") else fh
    if sys.version_info[0] == 2:
        if code.startswith('r'):
            ret = reader(fh)
        elif code.startswith('w'):
            ret = writer(fh)
        else:
            sys.stderr.write("I didn't understand code " + code + "\n")
            sys.exit(1)
    return ret


def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
    ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
    group = parser.add_mutually_exclusive_group()
    dest = arg if dest is None else dest
    group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
    group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)


class LimerickDetector:
    def __init__(self):
        """
        Initializes the object to have a pronunciation dictionary available
        """
        self._pronunciations = nltk.corpus.cmudict.dict()

    def num_syllables(self, word):
        """
        Returns the number of syllables in a word.  If there's more than one
        pronunciation, take the shorter one.  If there is no entry in the
        dictionary, return 1.
        """

        if word in self._pronunciations:
            twoli = self._pronunciations[word]
            # print twoli
            # print 'length of twoli', len(twoli)
            tp = []
            mahatp = []
            for ls in twoli:
                # print ls
                # print 'tp====', tp
                for x in ls:
                    # print x
                    if re.search(r'\d', x):
                        # print("Digit Found")
                        tp.append(x)
                        # print 'tp====', tp
                mahatp.append(len(tp))
                tp = []
            # print 'tp====', tp
            # print '--------------------------------------------------------------------'
            # print mahatp
            # print min(mahatp)
            return min(mahatp)
        return 1


    def rhymes(self, a, b):
        """
        Returns True if two words (represented as lower-case strings) rhyme,
        False otherwise.
        """

        if a not in self._pronunciations or b not in self._pronunciations:
            return False

        aPro = self._pronunciations[a]
        bPro = self._pronunciations[b]

        #print aPro
        #print bPro

        aTruncated = []
        flag = False
        for ls in aPro:
            tp = []
            for x in ls:
                if re.search(r'\d', x):
                    # print("Digit Found")
                    flag = True
                if (flag == True):
                    tp.append(x)
                    # print tp
            aTruncated.append(tp)
            flag = False
        #print aTruncated

        bTruncated = []
        flag = False
        for ls in bPro:
            tp = []
            for x in ls:
                if re.search(r'\d', x):
                    # print("Digit Found")
                    flag = True
                if (flag == True):
                    tp.append(x)
                    # print tp
            bTruncated.append(tp)
            flag = False
        #print bTruncated


        for lista in aTruncated:
            for listb in bTruncated:
                count = 0
                a = len(lista)
                b = len(listb)
                c = min(a, b)
                if (c == a):
                   # print 'I am in if'
                    smaller = lista
                    bigger = listb
                else:
                    #print 'i am in else'
                    smaller = listb
                    bigger = lista

                i = len(smaller) - 1
                j = len(bigger) - 1
                while (count < len(smaller)):

                    if (bigger[j] == smaller[i]):
                        i = i - 1
                        j = j - 1
                        count = count + 1
                    else:
                        break
                if (count == len(smaller)):
                    return True
        return False


    def is_limerick(self, text):
        """
        Takes text where lines are separated by newline characters.  Returns
        True if the text is a limerick, False otherwise.

        A limerick is defined as a poem with the form AABBA, where the A lines
        rhyme with each other, the B lines rhyme with each other, and the A lines do not
        rhyme with the B lines.


        Additionally, the following syllable constraints should be observed:
          * No two A lines should differ in their number of syllables by more than two.
          * The B lines should differ in their number of syllables by no more than two.
          * Each of the B lines should have fewer syllables than each of the A lines.
          * No line should have fewer than 4 syllables

        (English professors may disagree with this definition, but that's what
        we're using here.)


        """
        tokenized_lines = []
        lines = re.split("\n", text)

        tpline=[]
        for x in lines:
            x=re.sub(ur"[^\w\d'\s]+", '', x)
            tpline.append(x)


        #print 'Liness===',lines

        for line in tpline:
            # print line
            if word_tokenize(line) == []:
                continue
            tokenized_lines.append(word_tokenize(line))
        #print tokenized_lines

        #Converting to lower case

        for line in tokenized_lines:
            for x in line:
                x.lower()

        # Removing puntuations from the tokenized_lines





        global_sum = []
        for list in tokenized_lines:
            sum = 0
            for x in list:
                sum = sum + self.num_syllables(x)
            if sum !=0:
                global_sum.append(sum)

        #print 'Global=', global_sum

        # if not 5 lines
        if (len(global_sum) > 5 or len(global_sum) < 5):
            #print '1'
            return False

        # No line should have fewer than 4 syllables
        mini = min(global_sum)
        if (mini < 4):
            #print '2'
            return False

        a = global_sum[0] - global_sum[1]  # AA
        b = global_sum[0] - global_sum[4]  # AA
        c = global_sum[1] - global_sum[4]  # AA
        d = global_sum[2] - global_sum[3]  # BB

        if (a > 2 or a < -2 or b > 2 or b < -2 or c > 2 or c < -2 or d > 2 or d < -2):
            #print '3'
            return False

        # Each of the B lines should have fewer syllables than each of the A line

        if ((global_sum[2] > global_sum[0]) or (global_sum[2] > global_sum[1]) or (global_sum[2] > global_sum[4]) or (
            global_sum[3] > global_sum[0]) or (global_sum[3] > global_sum[1]) or (global_sum[3] > global_sum[4])):
            #print '4'
            return False

        firstA = tokenized_lines[0]
        secondA = tokenized_lines[1]
        thirdA = tokenized_lines[4]
        firstB = tokenized_lines[2]
        secondB = tokenized_lines[3]

        # print 'FirstAa=', firstA[-1]
        # print 'SecondA=', secondA
        # print 'ThirdA=', thirdA
        # print 'FirstB=', firstB
        # print 'SecondB=', secondB

        if not (self.rhymes(firstA[-1], secondA[-1])):  # First and Second A do not rhyme
            #print '5'
            return False

        if not (self.rhymes(secondA[-1], thirdA[-1])):  # Second and Third A do not match
            #print '6'
            return False

        if not (self.rhymes(firstA[-1], thirdA[-1])):  # First and Third A do not match
            #print '7'
            return False

        if not (self.rhymes(firstB[-1], secondB[-1])):  # B do not match
            #print '8'
            return False

        if (self.rhymes(firstA[-1], firstB[-1])):  # first A rhymed with first B
            #print '9'
            return False

        if (self.rhymes(secondA[-1], firstB[-1])):  # second A rhymed with first A
            #print '10'
            return False

        if (self.rhymes(thirdA[-1], firstB[-1])):  # third A rhymed with first B
            #print '11'
            return False

        if (self.rhymes(firstA[-1], secondB[-1])):  # first A rhymed with second B
            #print '12'
            return False

        if (self.rhymes(secondA[-1], secondB[-1])):  # second A rhymed with second B
            #print '13'
            return False

        if (self.rhymes(thirdA[-1], secondB[-1])):  # third A rhymed with second B
            #print '14'
            return False

        #print 'Reached here'
        return True

    def guess_syllables(self,word):
        words = list(word)
        # print 'Words=',words
        # print len(words)
        m = len(words) - 1

        for x in range(m, -1, -1):
            # print 'x=',x
            # print words[x]
            if (words[x] == words[x - 1]):
                words.pop(x)
            else:
                continue

        #print words

        final = ''.join(words)
        print final

        if final in self._pronunciations:
            return self.num_syllables(word)

        n = len(words) - 1
        vowels = ['a', 'e', 'i', 'o', 'u']
        count = 0
        for x in range(n, -1, -1):
            if x != 0:
                if words[x] in vowels and words[x - 1] not in vowels:
                    count = count + 1

        if (words[-1] == 'e'):
            count = count - 1

        if (words[-1] == 'y' and words[-2] not in vowels):
            count = count + 1

        #print 'Count==', count

        return count


    def apostrophe_tokenize(self,text):
        lines = re.split("\n", text)
        for x in lines:
            x.replace("'","")

        tokenized_lines=[]
        for line in lines:
            # print line
            if word_tokenize(line) == []:
                continue
            tokenized_lines.append(word_tokenize(line))






# The code below should not need to be modified
def main():
    parser = argparse.ArgumentParser(
        description="limerick detector. Given a file containing a poem, indicate whether that poem is a limerick or not",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    addonoffarg(parser, 'debug', help="debug mode", default=False)
    parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
    parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help="output file")

    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))

    infile = prepfile(args.infile, 'r')
    outfile = prepfile(args.outfile, 'w')

    ld = LimerickDetector()
    lines = ''.join(infile.readlines())
    outfile.write("{}\n-----------\n{}\n".format(lines.strip(), ld.is_limerick(lines)))


if __name__ == '__main__':
    main()


