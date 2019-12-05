# parsers.py
#
# Includes a few target functions for lxml parsers.
# PlaintextTarget: Produces plain text only
# StrandTarget: Produces data to be aligned with STRAND

import re
import tldextract

from io import StringIO
from urllib.parse import urlparse

# A base target class which assumes some tags will be ignored.
# This will output HTML with certain tags removed if used by itself.


class CleanupTarget(object):
    def __init__(self):
        self.buffer = StringIO()
        self.ignore_stack = []
        self.ignored_tags = {'script', 'style'}
        self.whitespace = re.compile("\s+", re.U)
#        self.word_break_tags = {'br', 'option', 'a'}
        self.word_break_tags = {'br', 'option'}
        self.sent_break_tags = {'td', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5',
                                'h6', 'title', 'hr', 'pre', 'blockquote', 'ul', 'li'}

    def start(self, tag, attrs):
        if tag in self.ignored_tags:
            self.ignore_stack.append(tag.lower())
        self.start_impl(tag, attrs)

    def end(self, tag):
        self.end_impl(tag)
        if len(self.ignore_stack) > 0 and tag.lower() == self.ignore_stack[-1]:
            self.ignore_stack.pop()

    def data(self, data):
        if len(self.ignore_stack) == 0:
            self.data_impl(data)

    def close(self):
        result = self.close_impl()
        self.buffer.close()
        self.buffer = StringIO()
        self.ignore_stack = []
        return result

    # Default implementation, just remove the ignored tags
    def start_impl(self, tag, attrs):
        if len(self.ignore_stack) == 0:
            if len(attrs) == 0:
                self.buffer.write("<%s>" % tag)
            else:
                self.buffer.write("<%s" % tag)
                for (attr, value) in attrs.iteritems():
                    self.buffer.write(" %s=\"%s\"" % (attr, value))
                self.buffer.write(">")

    def end_impl(self, tag):
        if len(self.ignore_stack) == 0:
            self.buffer.write("</%s>" % tag)

    def data_impl(self, data):
        self.buffer.write(data)

    def close_impl(self):
        return self.buffer.getvalue()

    # Remove unnecessary whitespace from the result
    def trimtext(self, text):
        result = StringIO()
        for line in text.split("\n"):
            line = line.strip()
            if len(line) == 0:
                continue
            result.write(self.format_whitespace(line) + "\n")
        return result.getvalue()

    # Converts all blocks of whitespace to a single space character
    def format_whitespace(self, text):
        return self.whitespace.sub(" ", text)


class PlaintextTarget(CleanupTarget):
    def __init__(self):
        super(PlaintextTarget, self).__init__()

    def start_impl(self, tag, attrs):
        if len(self.ignore_stack) == 0:
            if tag in self.word_break_tags:
                self.buffer.write(" ")
            if tag in self.sent_break_tags:
                self.buffer.write("\n")

    def end_impl(self, tag):
        if len(self.ignore_stack) == 0:
            if tag in self.word_break_tags:
                self.buffer.write(" ")
            if tag in self.sent_break_tags:
                self.buffer.write("\n")

    def data_impl(self, data):
        self.buffer.write(self.format_whitespace(data))

    def close_impl(self):
        return self.trimtext(self.buffer.getvalue())


class StrandTarget(CleanupTarget):
    def __init__(self, lang, align_href=False):
        super(StrandTarget, self).__init__()
        self.current_chunk = StringIO()
        # Tags which are not shown in the strand output. Taken from Herve's code.
        self.strand_ignore_tags = {'b', 'strong', 'i', 'em', 'font', 'span',
                                   'nobr', 'sup', 'sub', 'meta', 'link', 'acronym'}
        if not align_href:
            self.strand_ignore_tags.add('a')

        self.lang = lang
        self.align_href = align_href
        self.current_start_tag = None

        langlet = {"ja": ("ja", "jp", "jpn", "japanese", "japan"),
                   "en": ("en", "us", "eng", "english", "usa")}

        self.re_lang = re.compile(r"\b({:s})\b".format("|".join(langlet[lang])))
        self.re_slax = re.compile("(?<!:)/{2,}")

    def start_impl(self, tag, attrs):
        if len(self.ignore_stack) == 0:
            # If the tag is ignored by strand, it may still be used for whitespace
            # (but not for sentence breaking)
            if tag in self.strand_ignore_tags:
                if tag in self.word_break_tags:
                    self.current_chunk.write(" ")
            else:
                self.clear_current_chunk()
                if tag == "a" and self.align_href and "href" in attrs:
                    href = self.norm_lang(attrs["href"])
                    self.buffer.write(f"[START:a {href}]\n")
                    self.current_start_tag = "[START:a]"
                else:
                    self.buffer.write(f"[START:{tag}]\n")
                    self.current_start_tag = f"[START:{tag}]"

#                if tag != "a":
#                    self.buffer.write("[START:{:s}]\n".format(tag))
#                    self.current_start_tag = "[START:{:s}]".format(tag)
#                elif self.align_href and "href" in attrs and self.current_start_tag is not None:
#                    href = self.norm_lang(attrs["href"])
#                    val = self.buffer.getvalue()
#                    pos = val.rfind(self.current_start_tag)
#                    data = val[pos: pos + len(self.current_start_tag) - 1] + \
#                        " " + href + "]\n"
#                    self.buffer.seek(pos)
#                    self.buffer.write(data)

    def end_impl(self, tag):
        if len(self.ignore_stack) == 0:
            if tag in self.strand_ignore_tags:
                if tag in self.word_break_tags:
                    self.current_chunk.write(" ")
            else:
                self.clear_current_chunk()
                self.buffer.write("[END:%s]\n" % tag)
                #if tag != "a":
                #    self.clear_current_chunk()
                #    self.buffer.write("[END:%s]\n" % tag)
                self.current_start_tag = None

    def data_impl(self, data):
        self.current_chunk.write(self.format_whitespace(data))

    def close_impl(self):
        self.clear_current_chunk()
        return self.buffer.getvalue()

    # Write the current chunk to the output buffer if it's not empty
    def clear_current_chunk(self):
        if len(self.current_chunk.getvalue().strip()) > 0:
            chunk_str = self.format_whitespace(self.current_chunk.getvalue().strip())
            if len(chunk_str) > 0:
                self.buffer.write(chunk_str)
                self.buffer.write("\n")
            self.current_chunk.close()
            self.current_chunk = StringIO()

    def norm_lang(self, url):
        domain = tldextract.extract(url).domain
        path = urlparse(url).path
        path = self.re_lang.sub("", path)
        path = self.re_slax.sub("/", path)
        return domain + ":" + path


if __name__ == "__main__":
    import bs4
    import sys
    from lxml import etree

    def decode_html(html_string):
        converted = bs4.UnicodeDammit(html_string, isHTML=True)
        if not converted.unicode_markup:
            raise UnicodeDecodeError(
                "Failed to detect encoding, tried [%s]",
                ', '.join(converted.tried_encodings))
        return converted.unicode_markup

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

    if len(sys.argv) > 3:
        encoding = sys.argv[3]
    else:
        encoding = "utf8"
    html = open(sys.argv[1], encoding=encoding).read()
    parser = etree.HTMLParser(encoding=encoding, target=StrandTarget(sys.argv[2], True))

    tagchunks = apply_parser(html, parser)
    print(tagchunks)
