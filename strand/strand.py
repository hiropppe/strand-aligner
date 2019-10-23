#!/usr/bin/python

# strand.py
#
# An implementation of the STRAND HTML aligner as described in
# "The Web as a Parallel Corpus" (Resnik and Smith, 2003).

import numpy
import re

import py_aligner
import py_maxent

from scipy.stats import stats

class StrandAligner:
  def __init__(self, difference_threshold=0.1, confidence_min=0.95):
    # Maximum value for the difference percentage
    self.difference_threshold = difference_threshold
    # Minimum value for the confidence of the correlation between chunk lengths
    self.confidence_min = confidence_min
    self.me_model = py_maxent.PyMaxent(1.0)
    self.tag_matcher = re.compile(r"^\[(START|END):([^\]]+)\]$", re.U)
    self.pa = py_aligner.PyAligner()

  # Returns an alignment and an instance set for the maxent model
  def create_instance_set(self, source_stream, target_stream):
    # Dimensions of the alignment grid
    s_size = len(source_stream)
    t_size = len(target_stream)
    if s_size == 0 or t_size == 0:
      print "One or more of the input streams are empty"
      return ([], py_maxent.PyInstanceSet())
    # Compute the maximum deviation from the diagonal given the difference
    # percentage threshold
    max_difference = s_size + t_size

    (source, target) = self.tc_to_int(source_stream, target_stream)

    (alignment_cost, alignment) = self.pa.align(source, target)

    # Compute the difference percentage: the total number of mismatched tokens
    # divided by the maximum possible number of mismatched tokens
    difference_percentage = -float(alignment_cost)
    difference_percentage /= max_difference
    
    # Lengths of aligned source and target chunks, used in computing Pearson's
    # coefficient
    (s_chunk_lengths, t_chunk_lengths) = ([], [])
    result = []
    for (s, t) in alignment:
      if s >= 0 and t >= 0:
        result.append((source_stream[s], target_stream[t]))
        if source_stream[s].tc_type == TCType.CHUNK and target_stream[t].tc_type == TCType.CHUNK:
          s_chunk_lengths.append(source_stream[s].chunk_len)
          t_chunk_lengths.append(target_stream[t].chunk_len)
      elif s >= 0:
        result.append((source_stream[s], None))
      elif t >= 0:
        result.append((None, target_stream[t]))
    correlation, p_value = 0.0, 0.0
    if len(s_chunk_lengths) > 0:
      (correlation, p_value) = stats.pearsonr(s_chunk_lengths, t_chunk_lengths)
    #print "Correlation: %0.3f, p-value: %0.6f" % (correlation, p_value)

    # Create the instance set and return
    instance_set = py_maxent.PyInstanceSet()
    (parallel_instance, non_parallel_instance) = ([], [])
    #parallel_instance.append(("p_value_t", p_value))
    parallel_instance.append(("corr_t", correlation))
    #parallel_instance.append(("n_t", len(s_chunk_lengths)))
    parallel_instance.append(("diff_t", difference_percentage))
    parallel_instance.append(("bias_t", 1.0))
    #non_parallel_instance.append(("p_value_f", p_value))
    non_parallel_instance.append(("corr_f", correlation))
    #non_parallel_instance.append(("n_f", len(s_chunk_lengths)))
    non_parallel_instance.append(("diff_f", difference_percentage))
    non_parallel_instance.append(("bias_f", 1.0))
    instance_set.instances.append(parallel_instance)
    instance_set.instances.append(non_parallel_instance)
    return (result, instance_set)

  # Align two tag/chunk streams
  def align(self, source_stream, target_stream):
    #(alignment, instance_set) = self.create_instance_set(
    #    source_stream, target_stream)
    # TODO: Classify
    s_size = len(source_stream)
    t_size = len(target_stream)
    if s_size == 0 or t_size == 0:
      print "One or more of the input streams are empty"
      return []
    # Compute the maximum deviation from the diagonal given the difference
    # percentage threshold
    max_difference = s_size + t_size

    (source, target) = self.tc_to_int(source_stream, target_stream)

    (alignment_cost, alignment) = self.pa.align(source, target)
    # Lengths of aligned source and target chunks, used in computing Pearson's
    # coefficient
    result = []
    for (s, t) in alignment:
      if s >= 0 and t >= 0:
        result.append((source_stream[s], target_stream[t]))
      elif s >= 0:
        result.append((source_stream[s], None))
      elif t >= 0:
        result.append((None, target_stream[t]))
    return result

  # Creates maxent instance sets from a set of web page pairs. Source/target
  # docs are arrays of tagchunk streams, and labels is an array of Booleans
  # indicating whether or not they are actually parallel.
  def create_annotated_data(self, source_docs, target_docs, labels):
    assert len(source_docs) == len(target_docs)
    assert len(source_docs) == len(labels)
    data = []
    for i in xrange(0, len(source_docs)):
      (alignment, instance_set) = self.create_instance_set(
          source_docs[i], target_docs[i])
      if labels[i] == True:
        instance_set.true_instance = 0
      elif labels[i] == False:
        instance_set.true_instance = 1
      data.append(instance_set)
    return data
    
  # Create a list of tags/chunks from some iterable stream of lines
  def create_tag_chunk_stream(self, lines):
    tag_chunks = []
    for line in lines:
      line = line.strip()
      if len(line) == 0:
        continue
      m = self.tag_matcher.match(line)
      if m:
        tag_chunks.append(TagChunk(tag=m.group(2), tag_type=m.group(1)))
      else:
        tag_chunks.append(TagChunk(chunk_data=line))
    return tag_chunks

  # Converts arrays of tagchunks to arrays of integers to be used by the cython
  # aligner. Returns the two arrays as a tuple.
  def tc_to_int(self, source_tcs, target_tcs):
    tag_to_int = {}
    source = []
    target = []
    for s in source_tcs:
      if s.tc_type == TCType.START:
        if s.tag not in tag_to_int:
          tag_to_int[s.tag] = len(tag_to_int)
        source.append(2 + tag_to_int[s.tag])
      elif s.tc_type == TCType.END:
        if s.tag not in tag_to_int:
          tag_to_int[s.tag] = len(tag_to_int)
        # Assuming there are less than 2^16 unique HTML tags
        source.append(65536 + tag_to_int[s.tag])
      elif s.tc_type == TCType.CHUNK:
        source.append(1)
    for t in target_tcs:
      if t.tc_type == TCType.START:
        if t.tag not in tag_to_int:
          tag_to_int[t.tag] = len(tag_to_int)
        target.append(2 + tag_to_int[t.tag])
      elif t.tc_type == TCType.END:
        if t.tag not in tag_to_int:
          tag_to_int[t.tag] = len(tag_to_int)
        target.append(65536 + tag_to_int[t.tag])
      elif t.tc_type == TCType.CHUNK:
        target.append(1)
    return (source, target)

# An enum used by TagChunk
class TCType:
  START = 0
  END = 1
  CHUNK = 2

# TagChunks are the items aligned by STRAND.
class TagChunk:
  # Initialize a start or end tag
  def __init__(self, tag=None, tag_type=None, chunk_data=None):
    if tag and tag_type:
      self.tag = tag
      if tag_type == "START":
        self.tc_type = TCType.START
      elif tag_type == "END":
        self.tc_type = TCType.END
      else:
        raise Exception("Invalid TagChunk type: %s" % tag_type)
    elif chunk_data:
      self.tc_type = TCType.CHUNK
      self.chunk_len = len(chunk_data)
      self.chunk_data = chunk_data
    else:
      raise Exception("Invalid TagChunk init: tag=%s, tag_type=%s, chunk_data=%s"
          % (tag, tag_type, chunk_data))

  def __str__(self):
    if self.tc_type == TCType.START:
      return u"[START:%s]" % self.tag
    elif self.tc_type == TCType.END:
      return u"[END:%s]" % self.tag
    else:
      return u"[CHUNK:" + self.chunk_data + u"]"
  def __repr__(self):
    return self.__str__()
  def __unicode__(self):
    return self.__str__()
