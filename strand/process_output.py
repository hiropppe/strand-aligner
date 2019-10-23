#!/usr/bin/python

# process_output.py
#
# A program for processing and analyzing the output of parallel webpage mining
# on CommonCrawl.

import codecs
import errno
import itertools
import optparse
import os
import re
import sys

from random import shuffle
from StringIO import StringIO

# Used for parsing HTML
import bs4
import lxml.html
from lxml import etree

import parsers
import strand
from segmenter import Segmenter
from py_aligner import PyGaleChurchAligner

def main():
  parser = optparse.OptionParser()
  parser.add_option("-i", "--input-file", dest="input_file", default="",
      type="string", help="Location of the uncompressed mined webpages")
  parser.add_option("-n", "--num_entries", dest="num_entries", default=0,
      type="int", 
      help="Maximum number of entries to examine, set to 0 for no limit")
  parser.add_option("--language-pair", dest="language_pair",
      default="English,Spanish",
      help="Prints parallel data for the comma-separated language pair"
      + " when used with the --out-prefix option")

  parser.add_option("--out-prefix", dest="out_prefix", default="",
      help="Parallel data will be output to this location")

  parser.add_option("--annotate", dest="annotate", default="",
      help="Prints random pages to the given directory for annotation")
  parser.add_option("--annotate_amount", dest="annotate_amount", default=100,
      type="int", help="Number of document pairs to annotate")

  parser.add_option("--annotation_file", dest="annotation_file", default="",
      help="A file containing annotations of web page pairs")
  parser.add_option("--annotation_dir", dest="annotation_dir", default="",
      help="The location of the HTML for the annotated web pages")

  (opts, args) = parser.parse_args()

  # Initialize the HTML parsers
  cleanup_parser = etree.HTMLParser(encoding = "utf-8",
      target = parsers.CleanupTarget())
  plaintext_parser = etree.HTMLParser(encoding = "utf-8",
      target = parsers.PlaintextTarget())
  strand_parser = etree.HTMLParser(encoding = "utf-8",
      target = parsers.StrandTarget())
  # Gale Church aligner
  gc_aligner = PyGaleChurchAligner()
  strand_aligner = strand.StrandAligner()
  

  if opts.annotation_file and opts.annotation_dir:
    data = read_annotated_data(strand_aligner, strand_parser,
        opts.annotation_file, opts.annotation_dir)

    folds = 5
    features = []
    true_pos = 0
    false_pos = 0
    total_pos = 0
    correct = 0
    total = len(data)
    stats = {}
    for fold in xrange(0, folds):
      print "Fold %d:" % (fold + 1)
      training_data = []
      test_data = []
      for i in xrange(0, len(data)):
        if i % folds == fold:
          test_data.append(data[i])
        else:
          training_data.append(data[i])
      strand_aligner.me_model.set_training_data(training_data)
      strand_aligner.me_model.lbfgs_train()
      features.append(strand_aligner.me_model.get_features())
      for example in test_data:
        predicted_label = strand_aligner.me_model.get_label(example)
        true_label = example.true_instance
        print true_label, predicted_label
        print strand_aligner.me_model.get_probs(example)
        print example.instances[predicted_label]
        if true_label == 0:
          total_pos += 1
          if predicted_label == 0:
            true_pos += 1
        elif true_label != predicted_label:
          false_pos += 1
    correct = true_pos + total - total_pos - false_pos
    stats["Positives"] = total_pos
    stats["Accuracy"] = (100.0 * correct) / total
    stats["Precision"] = 0.0
    if true_pos + false_pos > 0:
      stats["Precision"] = (100.0 * true_pos) / (true_pos + false_pos)
    stats["Recall"] = (100.0 * true_pos) / total_pos
    stats["F1"] = 0.0
    if stats["Recall"] + stats["Precision"] > 0.0:
      stats["F1"] = 2 * stats["Precision"] * stats["Recall"] / (stats["Recall"]
          + stats["Precision"])
    for i in xrange(0, len(features)):
      print "Fold %d" % (i + 1)
      print features[i]
    print stats

  if opts.input_file == "":
    print "No input file given"
    return

  language_pair = None
  if opts.language_pair:
    languages = opts.language_pair.split(",")
    if len(languages) != 2:
      print "Error in language pair:", opts.language_pair
      return
    # TODO: Language codes
    language_pair = (languages[0], languages[1])

  data_to_annotate = []

  aligned_strand_out = None
  aligned_plaintext_out = None
  plaintext_docs_out = None
  segmenters = None
  if opts.out_prefix and language_pair:
    aligned_strand_out = []
    aligned_plaintext_out = []
    plaintext_docs_out = []
    segmenters = []
    for lang in language_pair:
      aligned_strand_out.append(codecs.open(
          "%s.strand.%s" % (opts.out_prefix, lang),
          encoding="utf-8", mode="w"))
      #aligned_plaintext_out.append(codecs.open(
      #    "%s.text.%s" % (opts.out_prefix, lang),
      #    encoding="utf-8", mode="w"))
      #plaintext_docs_out.append(codecs.open(
      #    "%s.docs.%s" % (opts.out_prefix, lang),
      #    encoding="utf-8", mode="w"))
      segmenters.append(Segmenter(lang))

  in_file = open(opts.input_file, "r")
  linecount = 0
  for line in in_file:
    (key, webpages) = parse_entry(line)
    if len(key) == 0:
      print "Malformed entry at line", linecount
    else:
      # default behavior for now: just print the URL
      #print url_to_filename(key).encode('utf-8')

      data_by_language = {}
      for webpage in webpages:
        if webpage['language'] not in data_by_language:
          data_by_language[ webpage['language'] ] = {}
        if opts.annotate:
          try:
            clean_html = apply_parser(webpage['html'], cleanup_parser)
            data_by_language[ webpage['language'] ]["html"] = clean_html
          except:
            pass

        if opts.out_prefix:
          #plaintext = apply_parser(webpage['html'], plaintext_parser)
          #data_by_language[ webpage['language'] ]["text"] = plaintext

          lang = webpage['language']
          if lang in language_pair:
            try:
              tagchunks = apply_parser(webpage['html'], strand_parser)
              data_by_language[lang]["strand"] = tagchunks
            except:
              pass

      if language_pair[0] in data_by_language and language_pair[1] in data_by_language:
        if opts.annotate:
          data_to_annotate.append((key,
              data_by_language[ language_pair[0] ]["html"],
              data_by_language[ language_pair[1] ]["html"]))
        if opts.out_prefix and ("strand" in
            data_by_language[ language_pair[0]]) and ("strand" in
            data_by_language[ language_pair[1]]):
          en_output = data_by_language[ language_pair[0] ]["strand"].split("\n")
          es_output = data_by_language[ language_pair[1] ]["strand"].split("\n")
          en_tagchunks = strand_aligner.create_tag_chunk_stream(en_output)
          es_tagchunks = strand_aligner.create_tag_chunk_stream(es_output)
          alignment = strand_aligner.align(en_tagchunks, es_tagchunks)
          for (s, t) in alignment:
            if (s and s.tc_type == strand.TCType.CHUNK
                and t and t.tc_type == strand.TCType.CHUNK):
              source_sents = segmenters[0].process(unicode(s.chunk_data))
              target_sents = segmenters[1].process(unicode(t.chunk_data))
              (cost, aligned_source, aligned_target) = gc_aligner.align(
                  source_sents, target_sents)
              for i in xrange(0, len(aligned_source)):
                s_sent = aligned_source[i]
                t_sent = aligned_target[i]
                if alpha_min_length(s_sent, t_sent) >= 5 and end_punc(s_sent, t_sent) == 1:
                  aligned_strand_out[0].write(s_sent + "\n")
                  aligned_strand_out[1].write(t_sent + "\n")
          # Plain text output and alignment (TODO)
          # Document output and alignment (TODO)

    linecount += 1
    if linecount == opts.num_entries:
      break
  in_file.close()

  if opts.out_prefix:
    for out_file in aligned_strand_out:
      out_file.close()
    for out_file in aligned_plaintext_out:
      out_file.close()
    for out_file in plaintext_docs_out:
      out_file.close()

  if opts.annotate:
    mkdir_p(opts.annotate)
    mkdir_p(opts.annotate + "/source")
    mkdir_p(opts.annotate + "/target")
    annotation_file = codecs.open(opts.annotate + "/annotation",
        encoding="utf-8", mode="w")
    shuffle(data_to_annotate)
    for i in xrange(0, opts.annotate_amount):
      (key, source, target) = data_to_annotate[i]
      count_str = "%04d_" % i
      out_source = codecs.open(opts.annotate + "/source/" + count_str +
          url_to_filename(key), encoding="utf-8", mode="w")
      out_target = codecs.open(opts.annotate + "/target/" + count_str +
          url_to_filename(key), encoding="utf-8", mode="w")
      out_source.write(source)
      out_target.write(target)
      annotation_file.write(key)
      annotation_file.write("\n\n")
      out_source.close()
      out_target.close()
    annotation_file.close()

# ----------------------------------------
# END MAIN
# ----------------------------------------

# Reads previously annotated data created with the "annotate" option.
def read_annotated_data(strand_aligner, strand_parser, annotation_file,
    annotation_dir):
  annotations = codecs.open(annotation_file, encoding="utf-8", mode="r")
  source_docs = []
  target_docs = []
  labels = []
  pos_count, neg_count, count = 0,0,0
  for webpage, answer in itertools.izip(annotations, annotations):
    key = url_to_filename(webpage.strip())
    tokens = answer.strip().split(" ")
    if tokens[0] == "yes":
      labels.append(True)
      pos_count += 1
    elif tokens[0] == "no":
      labels.append(False)
      neg_count += 1
    else:
      print "Error reading annotation token:", tokens[0]

    count_str = "%04d_" % count
    source_html = codecs.open(annotation_dir + "/source/" + count_str + key,
        encoding="utf-8", mode="r").read()
    target_html = codecs.open(annotation_dir + "/target/" + count_str + key,
        encoding="utf-8", mode="r").read()
    parsed_source = apply_parser(source_html, strand_parser).split("\n")
    parsed_target = apply_parser(target_html, strand_parser).split("\n")
    
    source_docs.append(strand_aligner.create_tag_chunk_stream(parsed_source))
    target_docs.append(strand_aligner.create_tag_chunk_stream(parsed_target))

    count += 1

  print "Positive examples:", pos_count
  print "Negative examples:", neg_count

  data = strand_aligner.create_annotated_data(source_docs, target_docs, labels)
  return data
    
# Usese BeautifulSoup to handle encodings (taken from lxml tutorial)
def decode_html(html_string):
  converted = bs4.UnicodeDammit(html_string, isHTML=True)
  if not converted.unicode_markup:
    raise UnicodeDecodeError(
      "Failed to detect encoding, tried [%s]",
      ', '.join(converted.tried_encodings))
  return converted.unicode_markup

# Passes the HTML through the given parser. Uses the BeautifulSoup parser as a
# failsafe.
def apply_parser(html, parser):
  result = ""
  try:
    result = etree.parse(StringIO(html), parser)
  except: # TODO: find the specific error
    try:
      result = etree.parse(StringIO(decode_html(html)), parser)
    except:
      soup = bs4.BeautifulSoup(html, "lxml")
      result = etree.parse(StringIO(str(soup)), parser)
      
  return result

# Parses a line of the tab-separated values file. Returns the key (a language
# independent URL) and a list of webpages (dicts with a url, language, and
# html). Returns an empty key on failure.
# The format is: key, (language, url, webpage){2,}
# The HTML will have both tabs and newlines escaped
def parse_entry(line):
  fields = line.split("\t")
  if len(fields) < 4 or ((len(fields) - 1) % 3) != 0:
    print "\n", len(fields)
    for field in fields:
      trunc = field
      if len(trunc) > 50:
        trunc = field[0:50]
      print "\t", trunc
    return ("", {})

  key = fields[0]
  offset = 1
  webpages = []
  while offset + 2 < len(fields):
    webpage = {}
    webpage['language'] = fields[offset]
    webpage['url'] = fields[offset+1]
    webpage['html'] = unescape_tabs_and_newlines(fields[offset+2])
    webpages.append(webpage)
    offset += 3

  return (key, webpages)

# Reverses the unescaping of newlines and tabs needed to store the HTML files
def unescape_tabs_and_newlines(str):
  return str.replace("\\t", "\t").replace("\\n", "\n")

# Converts a URL to a legal filename
def url_to_filename(url):
  result = url.replace("/", u"\u2044").replace("*", "\\*")
  return result + ".html"

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST:
      pass
    else: raise

def alpha_min_length(source, target):
  s_len = alpha_count(source.split(" "))
  t_len = alpha_count(target.split(" "))
  return min(s_len, t_len)

# Functions for pruning sentences
def end_punc(source, target):
  s_end = source[-1]
  t_end = target[-1]
  if re.match(r"[.?!]", s_end, re.U) and re.match(r"[.?!]", t_end, re.U):
    return 1
  else:
    return 0

# Other helper functions
def alpha_count(tokens):
  result = 0
  for token in tokens:
    if re.match(r"^\w+$", token, re.U):
      result += 1
  return result

if __name__ == "__main__":
  main()
