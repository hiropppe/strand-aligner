#!/usr/bin/python

# Runs STRAND on the gzipped output of the CommonCrawl miner.

import click
import codecs
import errno
import gzip
import os
import re

from io import StringIO

# Used for parsing HTML
import bs4
from lxml import etree

import parsers
import strand
from segmenter import Segmenter
from py_aligner import PyGaleChurchAligner


@click.command()
@click.option("--input-file", "-i", help="Location of the uncompressed mined webpages")
@click.option("--num-entries", "-n", help="Maximum number of entries to examine, set to 0 for no limit")
@click.option("--out-prefix", "-o", help="Parallel data will be output to this location")
@click.option("--sentence-aligner", "-sa", default=None, type=click.Choice(["GC"]), help="Sentence alignment implementation")
def main(input_file, num_entries, sentence_aligner, out_prefix):
    # Initialize the HTML parser and aligners
    strand_parser = etree.HTMLParser(encoding="utf-8",
                                     target=parsers.StrandTarget())
    if sentence_aligner == "GC":
        sent_aligner = PyGaleChurchAligner()
    else:
        sent_aligner = None

    strand_aligner = strand.StrandAligner()

    # Mapping from a full language name to a two letter code:
    lang_to_code = {"English": "en",
                    "Spanish": "es",
                    "French": "fr",
                    "German": "de",
                    "Czech": "cz",
                    "Russian": "ru",
                    "Korean": "ko",
                    "Arabic": "ar",
                    "Bengali": "bn",
                    "Bulgarian": "bg",
                    "Japanese": "ja",
                    "Kannada": "kn",
                    "Tamil": "ta",
                    "Telugu": "te",
                    "Urdu": "ur",
                    "Algerian Arabic": "arq",
                    "Chinese": "zh",
                    "Dari": "prs",
                    "Farsi": "fas",
                    "Kurdish": "ku",
                    "Kurdish Sorani": "ckb",
                    "Pashto": "ps",
                    "Somali": "so"}

    if input_file == "":
        print("No input file given")
        return

    if out_prefix == "":
        print("No output prefix given")
        return

    # Three output files per language pair (source, target, and annotation), one
    # segmenter per language, and one counter per language pair
    output_files = {}
    segmenters = {}
    line_counters = {}
    # We will always be working with English
    segmenters["en"] = Segmenter("English")

    in_file = gzip.open(input_file, "r")
    linecount = 0
    for line in in_file:
        line = line.decode("utf8")
        (key, webpages) = parse_entry(line)
        if len(key) == 0:
            print("Malformed entry at line", linecount)
        else:
            # default behavior for now: just print the URL
            # print(url_to_filename(key).encode('utf-8'))

            data_by_language = {}
            for webpage in webpages:
                if webpage['language'] not in data_by_language:
                    data_by_language[webpage['language']] = {}
                lang = webpage['language']
                data_by_language[lang]["url"] = webpage['url']
                try:
                    tagchunks = apply_parser(webpage['html'], strand_parser)
                    # print(tagchunks, file=open("{:s}.tagchunks.{:s}".format(
                    #     out_prefix, lang_to_code[lang]), "w"))
                    data_by_language[lang]["strand"] = tagchunks
                except:
                    print("Error parsing %s HTML at line %d" % (lang, linecount))
                    pass

            # if language_pair[0] in data_by_language and language_pair[1] in data_by_language:
            if "English" in data_by_language:
                target_lang = "English"
                target_code = lang_to_code[target_lang]
                # Loop over pairs
                for source_lang in data_by_language:
                    if source_lang == target_lang:
                        continue
                    source_code = lang_to_code[source_lang]
                    pair_code = "%s-%s" % (source_code, target_code)
                    # Check to see if we have initialized data for this pair
                    # Output files:
                    if pair_code not in output_files:
                        pair_files = {}
                        pair_files["bi"] = codecs.open(
                            "%s.%s" % (out_prefix, pair_code),
                            encoding="utf-8", mode="w")
                        pair_files["source"] = codecs.open(
                            "%s.%s.%s" % (out_prefix, pair_code, source_code),
                            encoding="utf-8", mode="w")
                        pair_files["target"] = codecs.open(
                            "%s.%s.%s" % (out_prefix, pair_code, target_code),
                            encoding="utf-8", mode="w")
                        pair_files["annotation"] = codecs.open(
                            "%s.%s.annotation" % (out_prefix, pair_code),
                            encoding="utf-8", mode="w")
                        output_files[pair_code] = pair_files
                    # Line counters
                    if pair_code not in line_counters:
                        line_counters[pair_code] = 0
                    # Sentence segmenters
                    if source_code not in segmenters:
                        segmenters[source_code] = Segmenter(source_lang)

                    source_strand = data_by_language[source_lang]["strand"].split("\n")
                    target_strand = data_by_language[target_lang]["strand"].split("\n")
                    (bi_sents, source_sents, target_sents, dp) = strand_extract_and_clean(
                        strand_aligner, sent_aligner, source_strand, target_strand,
                        segmenters[source_code], segmenters[target_code])

                    # If we have any data, write it along with the annotation
                    if len(source_sents) == len(target_sents) and len(source_sents) > 0:
                        bi_out = output_files[pair_code]["bi"]
                        print(dp, file=bi_out)
                        for b in bi_sents:
                            print("{:d}\t{:s}\t{:d}\t{:s}\t{:f}".format(
                                b[0], b[1], b[2], b[3], b[4]), file=bi_out)
                        source_out = output_files[pair_code]["source"]
                        for s in source_sents:
                            print(s, file=source_out)
                        target_out = output_files[pair_code]["target"]
                        for t in target_sents:
                            print(t, file=target_out)

                        current_offset = line_counters[pair_code]
                        increment = len(source_sents)

                        annotation_out = output_files[pair_code]["annotation"]
                        print("{:s}\t{:s}\t{:d}\t{:d}\t{:f}".format(data_by_language[source_lang]["url"],
                                                                    data_by_language[target_lang]["url"],
                                                                    current_offset,
                                                                    increment,
                                                                    dp), file=annotation_out)

                        line_counters[pair_code] += len(source_sents)

        linecount += 1
        if linecount == num_entries:
            break
    in_file.close()

    # Close files
    for pair in output_files:
        output_files[pair]["bi"].close()
        output_files[pair]["source"].close()
        output_files[pair]["target"].close()
        output_files[pair]["annotation"].close()

# ----------------------------------------
# END MAIN
# ----------------------------------------

# Run STRAND on the source and target HTML (parsed to tagchunks), and return the
# sentence pairs after filtering.


def strand_extract_and_clean(strand_aligner, sent_aligner, source, target, source_seg, target_seg):
    source_tagchunks = strand_aligner.create_tag_chunk_stream(source)
    target_tagchunks = strand_aligner.create_tag_chunk_stream(target)
   # print("STRAND alignment: %d x %d = %d" % (len(source_tagchunks),
   #     len(target_tagchunks), len(source_tagchunks) * len(target_tagchunks)))
    grid_size = len(source_tagchunks) * len(target_tagchunks)
    if grid_size > 1000000000:
        return ([], [])
    alignment, dp = strand_aligner.align(source_tagchunks, target_tagchunks)
    bi_out = []
    source_out = []
    target_out = []
    for (si, s, ti, t, c) in alignment:
        if (s and s.tc_type == strand.TCType.CHUNK
                and t and t.tc_type == strand.TCType.CHUNK):
            if sent_aligner is None:
                bi_out.append((si, s.chunk_data, ti, t.chunk_data, c))
                source_out.append(s.chunk_data)
                target_out.append(t.chunk_data)
            else:
                source_sents = source_seg.process(s.chunk_data)
                target_sents = target_seg.process(t.chunk_data)
                # print("GC alignment: %d x %d = %d" % (len(source_sents), len(
                #     target_sents), len(source_sents) * len(target_sents)))
                grid_size = len(source_sents) * len(target_sents)
                if grid_size > 1000000000:
                    continue
                (cost, aligned_source, aligned_target) = sent_aligner.align(
                    source_sents, target_sents)
                for i in range(0, len(aligned_source)):
                    s_sent = aligned_source[i]
                    t_sent = aligned_target[i]
                    # if s_sent != t_sent and alpha_min_length(s_sent, t_sent) >= 5 and end_punc(s_sent, t_sent) == 1:
                    if s_sent != t_sent:
                        bi_out.append((s_sent, t_sent, c))
                        source_out.append(s_sent)
                        target_out.append(t_sent)
    return (bi_out, source_out, target_out, dp)

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
    except:  # TODO: find the specific error
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
        print("\n", len(fields))
        for field in fields:
            trunc = field
            if len(trunc) > 50:
                trunc = field[0:50]
            print("\t", trunc)
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
        else:
            raise


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
