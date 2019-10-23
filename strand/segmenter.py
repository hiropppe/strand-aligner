#!/usr/bin/python

# segmenter.py
#
# Sentence breaking using NLTK

import nltk
import nltk.data
import nltk.tokenize.punkt

class Segmenter:
  def __init__(self, language):
    sbreak_path = "tokenizers/punkt/" + language.lower() + ".pickle"
    try:
      self.sent_breaker = nltk.data.load(sbreak_path)
    except(LookupError):
      print "Unable to find sentence breaking model for", language
      self.sent_breaker = nltk.data.load("tokenizers/punkt/english.pickle")
    
  # Perform sentence breaking on a line of text and return an array of sentences
  def process(self, line):
    return self.sent_breaker.tokenize(line.strip());

def main():
  import codecs
  import sys
  text_filename = sys.argv[1]
  language = sys.argv[2]
  text_file = codecs.open(text_filename, encoding='utf-8', mode='r')
  segmenter = Segmenter(language)
  for line in text_file:
    sentences = segmenter.process(line)
    for sentence in sentences:
      print sentence.encode('utf-8')
  text_file.close()


if __name__ == "__main__":
  main()
