#include <cstdlib>

#include <iostream>
#include <vector>
#include <utility>

#include "aligner.h"
#include "gale_church_aligner.h"

using namespace std;

int main(int argc, char** argv) {
  srand(time(NULL));
  vector<int> source, target;
  int s_size = 1500;
  int t_size = 2000;
  for (int s = 0; s < s_size; ++s) {
    source.push_back((rand() % 10) + 1);
    cout << source[s] << " ";
  }
  cout << endl;
  for (int t = 0; t < t_size; ++t) {
    target.push_back((rand() % 10) + 1);
    cout << target[t] << " ";
  }
  cout << endl;
  GaleChurchAligner* aligner = new GaleChurchAligner();
  vector<AlignmentBead> alignment;
  int score = aligner->align(source, target, &alignment);
  cout << "Alignment score: " << score << endl;
  for (int i = 0; i < alignment.size(); ++i) {
    cout << "(" << alignment[i].s_start << ", " << alignment[i].s_end << ") ("
        << alignment[i].t_start << ", " << alignment[i].t_end << ")" << endl;
  }

  delete aligner;
}
