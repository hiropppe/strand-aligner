# distutils: language = c++
# distutils: sources = aligner.cpp gale_church_aligner.cpp

from libcpp.vector cimport vector
from libcpp.utility cimport pair
import re

cdef extern from "aligner.h":
  cdef cppclass Aligner:
    Aligner() except +
    int align(vector[int]&, vector[int]&, vector[pair[int, int] ]*)
    int s_size, t_size

cdef extern from "gale_church_aligner.h":
  struct AlignmentBead:
    int s_start
    int s_end
    int t_start
    int t_end
  cdef cppclass GaleChurchAligner:
    GaleChurchAligner() except +
    double align(vector[int]&, vector[int]&, vector[AlignmentBead]*)

cdef class PyAligner:
  cdef Aligner *thisptr
  def __cinit__(self):
    self.thisptr = new Aligner()
  def __dealloc__(self):
    del self.thisptr
  # Returns a tuple: (alignment_cost, alignment)
  # where the alignment is a list of aligned source/target indices (-1 is used
  # in the source or target for insertions/deletions)
  def align(self, source, target):
    cdef int i
    cdef vector[int] source_vec
    for i in source:
      source_vec.push_back(i)
    cdef vector[int] target_vec
    for i in target:
      target_vec.push_back(i)
    cdef vector[pair[int, int] ] alignment_vec
    cdef int cost = self.thisptr.align(source_vec, target_vec, &alignment_vec)
    alignment = []
    for i in xrange(0, alignment_vec.size()):
      alignment.append((alignment_vec[i].first, alignment_vec[i].second))
    return (cost, alignment)

cdef class PyGaleChurchAligner:
  cdef GaleChurchAligner* thisptr
  def __cinit__(self):
    self.thisptr = new GaleChurchAligner()
  def __dealloc__(self):
    del self.thisptr
  # Returns a tuple: (alignment_cost, source_sentences, target_sentences)
  # where the source and target sentences are lists of the same length that have
  # been aligned (one side may contain empty strings)
  def align(self, source, target):
    remove_ws = re.compile(r"[\s\r\n]+");
    cdef vector[int] source_vec
    for sent in source:
      source_vec.push_back(len(remove_ws.sub("", sent)))
    cdef vector[int] target_vec
    for sent in target:
      target_vec.push_back(len(remove_ws.sub("", sent)))
    cdef vector[AlignmentBead] alignment
    cdef double cost = self.thisptr.align(source_vec, target_vec, &alignment)
    aligned_source = []
    aligned_target = []
    cdef int i, s, t
    cdef AlignmentBead bead
    for i in xrange(0, alignment.size()):
      bead = alignment[i]
      source_sent = ""
      for s in xrange(bead.s_start, bead.s_end):
        if len(source_sent) == 0:
          source_sent = source[s].strip()
        else:
          source_sent += " " + source[s].strip()
      target_sent = ""
      for t in xrange(bead.t_start, bead.t_end):
        if len(target_sent) == 0:
          target_sent = target[t].strip()
        else:
          target_sent += " " + target[t].strip()
      aligned_source.append(source_sent)
      aligned_target.append(target_sent)
    return (cost, aligned_source, aligned_target)
