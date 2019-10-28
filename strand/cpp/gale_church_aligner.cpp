#include "gale_church_aligner.h"

#include <algorithm>
#include <iostream>
#include <limits>

using std::cout;
using std::endl;

double GaleChurchAligner::align(vector<int>& source, vector<int>& target,
    vector<AlignmentBead>* alignment) {
  s_size = source.size();
  t_size = target.size();
  double* grid = new double[idx(s_size, t_size)+1];
  int8_t* backpointers = new int8_t[idx(s_size, t_size)+1];
  for (int s = 0; s <= s_size; ++s) {
    for (int t = 0; t <= t_size; ++t) {
      double best_score = -std::numeric_limits<double>::max();
      if ((s == 0) && (t == 0)) {
        best_score = 0.0;
      }
      for (int a = 0; a < ALIGNMENT_TYPES; ++a) {
        int old_s = s - alignment_types[a].s;
        int old_t = t - alignment_types[a].t;
        if ((old_s < 0) || (old_t < 0)) {
          continue;
        }
        double score = grid[idx(old_s, old_t)] + alignment_types[a].cost;
        //if ((s - old_s > 0) && (t - old_t > 0)) {
          int s_len = 0;
          for (int i = old_s; i < s; ++i) {
            s_len += source[i];
          }
          int t_len = 0;
          for (int i = old_t; i < t; ++i) {
            t_len += target[i];
          }
          score += alignment_cost(s_len, t_len);
        //}
        if (score > best_score) {
          best_score = score;
          backpointers[idx(s,t)] = a;
        }
      } // END loop over alignment types
      grid[idx(s,t)] = best_score;
    }
  }
  double result = grid[idx(s_size, t_size)];
  int s = s_size;
  int t = t_size;
  alignment->clear();
  while ((s > 0) && (t > 0)) {
    AlignmentType at = alignment_types[backpointers[idx(s,t)] ];
    AlignmentBead bead;
    bead.s_start = s - at.s;
    bead.s_end = s;
    bead.t_start = t - at.t;
    bead.t_end = t;
    alignment->push_back(bead);
    s -= at.s;
    t -= at.t;
  }
  std::reverse(alignment->begin(), alignment->end());
  delete[] grid;
  delete[] backpointers;
  return result;
}
