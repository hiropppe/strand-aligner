#!/usr/bin/python

# segmenter.py
#
# Sentence breaking using NLTK

import nltk

from nltk.tokenize import PunktSentenceTokenizer


class Segmenter:
    def __init__(self, language):
        if language.lower() == "japanese":
            self.sent_breaker = nltk.RegexpTokenizer(u'[^　！？。]*[！？。.\n]')
        else:
            nltk.download("punkt")
            self.sent_breaker = PunktSentenceTokenizer()

    # Perform sentence breaking on a line of text and return an array of sentences
    def process(self, line):
        return self.sent_breaker.tokenize(line.strip())


def main():
    import sys
    text_filename = sys.argv[1]
    language = sys.argv[2]
    text_file = open(text_filename, encoding='utf-8', mode='r')
    segmenter = Segmenter(language)
    for line in text_file:
        sentences = segmenter.process(line)
        for sentence in sentences:
            print(sentence)
    text_file.close()


if __name__ == "__main__":
    main()
