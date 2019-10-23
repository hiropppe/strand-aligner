/*
 * This is only a small test of the cpp code with dummy data
 */

#include <cstdlib>
#include <iostream>
#include <vector>
#include <utility>

#include "cpp/maxent/maxent.h"

using namespace std;

int main(int argc, char **argv) {
  srand(time(NULL));

  vector<InstanceSet>* data = new vector<InstanceSet>();
  for (int i = 0; i < 100000; ++i) {
    // Create a new data point.
    InstanceSet is;
    is.true_instance = 0;
    MaxentInstance true_example, false_example;
    true_example.push_back(make_pair("pos_feature", 6.0 - ((rand() % 10) / 1.0)));
    true_example.push_back(make_pair("neg_feature", -1.0 + ((rand() % 2) / 1.0)));
    true_example.push_back(make_pair("dummy", 1.0));
    //false_example["pos_feature"] = -0.5 + ((rand() % 10) / 1.0);
    //false_example["neg_feature"] = 2.0 + ((rand() % 2) / 1.0);
    false_example.push_back(make_pair("dummy", 1.0));
    is.instances.push_back(true_example);
    is.instances.push_back(false_example);
    data->push_back(is);
  }

  MaxentModel mm(1.0);
  mm.set_training_data(data);
  mm.lbfgs_train();
  mm.print_weights(cout);
  vector<pair<string, double> > features;
  mm.get_features(&features);
  vector<pair<string, double> >::iterator it;
  for (it = features.begin(); it != features.end(); ++it) {
    cout << it->first << " " << it->second << endl;
  }
}
