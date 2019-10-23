#ifndef __MAXENT_H__
#define __MAXENT_H__

#include <iostream>
#include <string>
#include <tr1/unordered_map>
#include <vector>
#include <utility>

#include "lbfgs.h"

using std::string;
using std::tr1::unordered_map;
using std::vector;
using std::pair;

// A featurized (x, y) pair.
typedef vector<pair<string, double> > MaxentInstance;

// A set of (x, y) pairs where only the y's differ. Can contain an optional
// label (true_instance) for the correct instance (-1 if it's unlabeled).
struct InstanceSet {
  vector<MaxentInstance> instances;
  int true_instance;
};

/*
 * A generic maxent model. Uses L-BFGS for optimization.
 */

class MaxentModel {
 public:
  MaxentModel(double l2 = 0.0) : l2_norm(l2), training_data(NULL) {}
  ~MaxentModel() {
    if (training_data != NULL) {
      delete training_data;
    }
  }

  // The L-BFGS module must have access to the training data while optimizing,
  // so this must be done before lbfgs_train.
  // Ownership of "data" is transfered to this object.
  void set_training_data(vector<InstanceSet>* data);
  // Train on the current data using lib-lbfgs, and return its status code.
  int lbfgs_train();
  // Create space in the weight vector for the features that fire on this data.
  void init_feature_weights(const vector<InstanceSet>* data);

  // Return the probability of one of the members of an instance.
  double get_prob(const InstanceSet& instance_set, int index);

  // Populates the "probs" vector with the probabilities of all members of the
  // instance set.
  void get_probs(const InstanceSet& instance_set, vector<double>* probs);

  // Returns the index of the highest scoring instance in the given set. Does
  // not compute probabilities.
  int get_label(const InstanceSet& instance_set);

  // Test the model on a set of annotated data, returning the accuracy
  double test(const vector<InstanceSet>& data);

  // Get the names/weights of all features
  void get_features(vector<pair<string, double> >* features);

  // Print the feature weights/names to the given stream
  void print_weights(std::ostream& out);

 private:
  // Functions for interfacing with lib-lbfgs
  static lbfgsfloatval_t _evaluate(void *instance, const lbfgsfloatval_t *x,
      lbfgsfloatval_t *g, const int n, const lbfgsfloatval_t step) {
      return reinterpret_cast<MaxentModel*>(instance)->evaluate(x, g, n, step);
  }
  // Computes the objective function and gradient
  lbfgsfloatval_t evaluate(const lbfgsfloatval_t *x, lbfgsfloatval_t *g,
      const int n, const lbfgsfloatval_t step);
  static int _progress(void *instance, const lbfgsfloatval_t *x, const lbfgsfloatval_t *g,
      const lbfgsfloatval_t fx, const lbfgsfloatval_t xnorm, const lbfgsfloatval_t gnorm,
      const lbfgsfloatval_t step, int n, int k, int ls) {
    return reinterpret_cast<MaxentModel*>(instance)->progress(x, g, fx, xnorm, gnorm, step, n, k, ls);
  }
  int progress(const lbfgsfloatval_t *x, const lbfgsfloatval_t *g, 
      const lbfgsfloatval_t fx, const lbfgsfloatval_t xnorm,
      const lbfgsfloatval_t gnorm, const lbfgsfloatval_t step, int n, int k, int ls);

  // Compute the gradient of the objective function on the given set of labeled
  // data, and return the value of the objective function.
  double compute_gradient(const vector<InstanceSet>& data,
      vector<double>* gradient);

  // Compute the normalizing constant for the given instance set
  double compute_z(const InstanceSet& instance_set);

  // Returns an informative error message from lib-lbfgs's error codes. Taken from
  // https://github.com/redpony/creg
  const char* error_name(int lbfgs_ret);

  // Used for storing the feature weights
  unordered_map<string, int> feature_index;
  vector<double> feature_weights;
  // Weight of the L2 regularization parameter
  double l2_norm;
  // Pointer to the training data, used during L-BFGS
  vector<InstanceSet>* training_data;
};

#endif
