#!/usr/bin/python

from py_aligner import PyGaleChurchAligner
import sys
import codecs

def main():
  source_file = codecs.open(sys.argv[1], encoding="utf-8", mode="r")
  target_file = codecs.open(sys.argv[2], encoding="utf-8", mode="r")
  source_out = codecs.open(sys.argv[3], encoding="utf-8", mode="w")
  target_out = codecs.open(sys.argv[4], encoding="utf-8", mode="w")

  #source = [line.lstrip() for line in source_file.readlines()]
  #target = [line.lstrip() for line in target_file.readlines()]
  source = source_file.readlines()
  target = target_file.readlines()

  aligner = PyGaleChurchAligner()
  (cost, aligned_source, aligned_target) = aligner.align(source, target)
  print cost, len(aligned_source), len(aligned_target)
  for i in xrange(0, len(aligned_source)):
    source_out.write(aligned_source[i] + "\n")
    target_out.write(aligned_target[i] + "\n")
  source_file.close()
  target_file.close()
  source_out.close()
  target_out.close()

if __name__ == "__main__":
  main()
