#ifndef __GALE_CHURCH_ALIGNER_H__
#define __GALE_CHURCH_ALIGNER_H__

/*
* gale_church_aligner.h
*
* An implementation of Gale and Church sentence alignment based on
* sentence-align-corpus.perl
*
*/

#include <cmath>
#include <vector>

#define ALIGNMENT_TYPES 5
#define MAX_ALIGNMENT_COST -25

using std::pair;
using std::vector;

struct AlignmentType {
  int s; // Number of source sentences
  int t; // Number of target sentences
  double cost; // Prior
};

struct AlignmentBead {
  int s_start;
  int s_end;
  int t_start;
  int t_end;
};

class GaleChurchAligner {
 public:
  GaleChurchAligner() {
    // Initialize alignment types/priors
    alignment_types[0].s = 1; alignment_types[0].t = 1; alignment_types[0].cost = log(0.89);
    alignment_types[1].s = 1; alignment_types[1].t = 0; alignment_types[1].cost = log(0.005);
    alignment_types[2].s = 0; alignment_types[2].t = 1; alignment_types[2].cost = log(0.005);
    alignment_types[3].s = 2; alignment_types[3].t = 1; alignment_types[3].cost = log(0.0445);
    alignment_types[4].s = 1; alignment_types[4].t = 2; alignment_types[4].cost = log(0.0445);
  }
  ~GaleChurchAligner() {}

  // Aligns the source and target vectors containing the lengths of the
  // sentences, populates the alignment vector, and returns the cost of the
  // alignment. Each item in the alignment is a pair of source and target
  // ranges.
  double align(vector<int>& source, vector<int>& target,
      vector<AlignmentBead>* alignment);
 
 private:
  inline int idx(int s, int t) {
    return (s * (t_size + 1)) + t;
  }
  int s_size;
  int t_size;
  // The costs for 0-1, 1-0, 1-1 (etc.) alignments.
  AlignmentType alignment_types[ALIGNMENT_TYPES];

  // Gives the cost for aligning sentences based on their length. Taken straight
  // from the C code
  inline double alignment_cost(int s_len, int t_len) {
    double z, pd, mean;
    double c = 1.0;
    double s2 = 6.8;
    if ((s_len == 0) && (t_len == 0)) {
      return 0.0;
    }
    mean = (s_len + (t_len/c)) / 2.0;
    z = ((c * s_len) - t_len) / sqrt(s2 * mean);
    if (z < 0.0) {
      z = -z;
    }
    pd = 2.0 * (1.0 - pnorm(z));
    if (pd > 0.0) {
      return log(pd);
    } else {
      return MAX_ALIGNMENT_COST;
    }
  }
  inline double pnorm(double z) {
    double t = 1.0 / (1.0 + 0.2316419 * z);
    return 1.0 - 0.3989423 * exp(-z * z / 2) *
        ((((1.330274429 * t 
        - 1.821255978) * t 
        + 1.781477937) * t 
        - 0.356563782) * t
        + 0.319381530) * t;
  }

};

#endif
