#include "aligner.h"

#include <algorithm>
#include <cassert>

using std::make_pair;
using std::max;

int Aligner::align(vector<int>& source, vector<int>& target,
    vector<pair<int, int> >* alignment) {

  // Sizes used for the alignment grid
  s_size = source.size();
  t_size = target.size();
  int* grid = new int[idx(s_size, t_size)+1];

  for (int s = 0; s <= s_size; ++s) {
    for (int t = 0; t <= t_size; ++t) {
      int best_score = -1 * (s_size + t_size);
      if ((s == 0) && (t == 0)) {
        best_score = 0;
      }
      if (s > 0) {
        best_score = max(best_score, grid[idx(s-1,t)] + cost(source[s-1],0));
      }
      if (t > 0) {
        best_score = max(best_score, grid[idx(s,t-1)] + cost(0,target[t-1]));
      }
      if ((s > 0) && (t > 0)) {
        best_score = max(best_score,
            grid[idx(s-1,t-1)] + cost(source[s-1],target[t-1]));
      }
      grid[idx(s,t)] = best_score;
    }
  }
  int score = grid[idx(s_size, t_size)];

  // Create the alignment by walking backwards from the end
  alignment->clear();
  int i = s_size;
  int j = t_size;
  while ((i > 0) || (j > 0)) {
    int current_score = grid[idx(i,j)];
    if (i > 0) {
      if (current_score == (grid[idx(i-1,j)] + cost(source[i-1],0))) {
        --i;
        alignment->push_back(make_pair(i,-1));
        continue;
      }
    }
    if (j > 0) {
      if (current_score == (grid[idx(i,j-1)] + cost(0,target[j-1]))) {
        --j;
        alignment->push_back(make_pair(-1,j));
        continue;
      }
    }
    if ((i > 0) && (j > 0)) {
      if (current_score ==
          (grid[idx(i-1,j-1)] + cost(source[i-1],target[j-1]))) {
        --i;
        --j;
        alignment->push_back(make_pair(i,j));
        continue;
      }
    }
    assert(0);
  }

  delete[] grid;

  std::reverse(alignment->begin(), alignment->end());
  return score;
}
