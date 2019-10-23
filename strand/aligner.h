#ifndef __ALIGNER_H__
#define __ALIGNER_H__

/*
* Aligner.h
*
* A basic dynamic programming aligner for vectors of integers. The integers must
* be greater than 0, and they are considered to match if they are equal.
*
*/

#include <utility>
#include <vector>

using std::vector;
using std::pair;

class Aligner {
 public:
  Aligner() {}
  ~Aligner() {}

  // Align the two sequences and return the number of mismatches in the
  // alignment. The alignment vector is populated with source/target index pairs
  int align(vector<int>& source, vector<int>& target,
      vector<pair<int, int> >* alignment);
 
 private:
  inline int cost(int x, int y) {
    if ((x == 0) || (y == 0)) {
      return -1;
    } else if (x != y) {
      return -2;
    } else {
      return 0;
    }
  }
  inline int idx(int s, int t) {
    return (s * (t_size + 1)) + t;
  }
  int s_size;
  int t_size;

};

#endif
