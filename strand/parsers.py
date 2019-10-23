#!/usr/bin/python

# parsers.py
#
# Includes a few target functions for lxml parsers.
# PlaintextTarget: Produces plain text only
# StrandTarget: Produces data to be aligned with STRAND

import re
from StringIO import StringIO

# A base target class which assumes some tags will be ignored.
# This will output HTML with certain tags removed if used by itself.
class CleanupTarget(object):
  def __init__(self):
    self.buffer = StringIO()
    self.ignore_stack = []
    self.ignored_tags = {'script', 'style'}
    self.whitespace = re.compile("\s+", re.U)
    self.word_break_tags = {'br', 'option', 'a'}
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
  def __init__(self):
    super(StrandTarget, self).__init__()
    self.current_chunk = StringIO()
    # Tags which are not shown in the strand output. Taken from Herve's code.
    self.strand_ignore_tags = {'a', 'b', 'strong', 'i', 'em', 'font', 'span',
        'nobr', 'sup', 'sub', 'meta', 'link', 'acronym'}

  def start_impl(self, tag, attrs):
    if len(self.ignore_stack) == 0:
      # If the tag is ignored by strand, it may still be used for whitespace
      # (but not for sentence breaking)
      if tag in self.strand_ignore_tags:
        if tag in self.word_break_tags:
          self.current_chunk.write(" ")
      else:
        self.clear_current_chunk()
        self.buffer.write("[START:%s]\n" % tag)
  def end_impl(self, tag):
    if len(self.ignore_stack) == 0:
      if tag in self.strand_ignore_tags:
        if tag in self.word_break_tags:
          self.current_chunk.write(" ")
      else:
        self.clear_current_chunk()
        self.buffer.write("[END:%s]\n" % tag)
  def data_impl(self, data):
    self.current_chunk.write(self.format_whitespace(data))
  def close_impl(self):
    self.clear_current_chunk()
    return self.buffer.getvalue()

  # Write the current chunk to the output buffer if it's not empty
  def clear_current_chunk(self):
    if self.current_chunk.len > 0:
      chunk_str = self.format_whitespace(self.current_chunk.getvalue().strip())
      if len(chunk_str) > 0:
        self.buffer.write(chunk_str)
        self.buffer.write("\n")
      self.current_chunk.close()
      self.current_chunk = StringIO()
