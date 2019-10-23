#include "cpp/maxent/maxent.h"

#include <cmath>
#include <cstdlib>
#include <cstdio>

#include <iostream>
#include <limits>

#include "cpp/util/math_util.h"

using std::string;
using std::tr1::unordered_map;
using std::vector;

using std::cout;
using std::endl;

void MaxentModel::set_training_data(vector<InstanceSet>* data) {
  init_feature_weights(data);
  if (training_data != NULL) {
    delete training_data;
  }
  training_data = data;
}

int MaxentModel::lbfgs_train() {
  lbfgsfloatval_t objective;
  lbfgsfloatval_t *weights = lbfgs_malloc(feature_weights.size());
  for (int i = 0; i < feature_weights.size(); ++i) {
    weights[i] = feature_weights[i];
  }

  int ret = lbfgs(feature_weights.size(), weights, &objective, _evaluate,
    _progress, this, NULL);

  cout << "L-BFGS optimization terminated with status code " << ret << endl;
  cout << error_name(ret) << endl;
  cout << "Objective function value: " << objective << endl;

  for (int i = 0; i < feature_weights.size(); ++i) {
    feature_weights[i] = weights[i];
  }

  lbfgs_free(weights);
  return ret;
}

void MaxentModel::init_feature_weights(const vector<InstanceSet>* data) {
  for (int i = 0; i < data->size(); ++i) {
    for (int j = 0; j < data->at(i).instances.size(); ++j) {
      const MaxentInstance& instance = data->at(i).instances[j];
      MaxentInstance::const_iterator it;
      for (it = instance.begin(); it != instance.end(); ++it) {
        if (feature_index.find(it->first) == feature_index.end()) {
          feature_index[it->first] = feature_weights.size();
          feature_weights.push_back(0.1);
        }
      }
    }
  }
}

double MaxentModel::get_prob(const InstanceSet& instance_set, int index) {
  double prob = 0.0;
  double z = compute_z(instance_set);
  MaxentInstance::const_iterator it;
  const MaxentInstance& instance = instance_set.instances.at(index);
  for (it = instance.begin(); it != instance.end(); ++it) {
    int f_i = feature_index[it->first];
    prob += it->second * feature_weights[f_i];
  }
  return exp(prob) / z;
}

void MaxentModel::get_probs(const InstanceSet& instance_set,
    vector<double>* probs) {
  probs->resize(instance_set.instances.size(), 0.0);
  double z = 0.0;
  MaxentInstance::const_iterator it;
  for (int i = 0; i < instance_set.instances.size(); ++i) {
    const MaxentInstance& instance = instance_set.instances.at(i);
    for (it = instance.begin(); it != instance.end(); ++it) {
      int f_i = feature_index[it->first];
      (*probs)[i] += it->second * feature_weights[f_i];
    }
    (*probs)[i] = exp((*probs)[i]);
    z += (*probs)[i];
  }
  for (int i = 0; i < instance_set.instances.size(); ++i) {
    (*probs)[i] /= z;
  }
}

int MaxentModel::get_label(const InstanceSet& instance_set) {
  int best_label = -1;
  int best_score = -std::numeric_limits<double>::max();
  MaxentInstance::const_iterator it;
  for (int i = 0; i < instance_set.instances.size(); ++i) {
    double score = 0.0;
    const MaxentInstance& instance = instance_set.instances.at(i);
    for (it = instance.begin(); it != instance.end(); ++it) {
      int f_i = feature_index[it->first];
      score += it->second * feature_weights[f_i];
    }
    if (score > best_score) {
      best_score = score;
      best_label = i;
    }
  }
  return best_label;
}

double MaxentModel::test(const vector<InstanceSet>& data) {
  int num_correct = 0;
  for (int i = 0; i < data.size(); ++i) {
    int label = get_label(data.at(i));
    if (label == data.at(i).true_instance) {
      ++num_correct;
    }
  }

  if (data.size() > 0) {
    return (double) num_correct / (double) data.size();
  } else {
    return 0.0;
  }
}

void MaxentModel::get_features(vector<pair<string, double> >* features) {
  features->clear();
  unordered_map<string, int>::iterator it;
  for (it = feature_index.begin(); it != feature_index.end(); ++it) {
    features->push_back(make_pair(it->first, feature_weights[it->second]));
  }
}

void MaxentModel::print_weights(std::ostream& out) {
  unordered_map<string, int>::iterator it;
  for (it = feature_index.begin(); it != feature_index.end(); ++it) {
    out << it->first << "\t" << feature_weights[it->second] << std::endl;
  }
}

lbfgsfloatval_t MaxentModel::evaluate(const lbfgsfloatval_t *x, lbfgsfloatval_t *g,
    const int n, const lbfgsfloatval_t step) {
  for (int i = 0; i < n; ++i) {
    feature_weights[i] = x[i];
  }
  vector<double> gradient;
  double objective = compute_gradient(*training_data, &gradient);
  for (int i = 0; i < n; ++i) {
    g[i] = gradient[i];
  }
  return objective;
}

int MaxentModel::progress(const lbfgsfloatval_t *x, const lbfgsfloatval_t *g, 
    const lbfgsfloatval_t fx, const lbfgsfloatval_t xnorm,
    const lbfgsfloatval_t gnorm, const lbfgsfloatval_t step, int n, int k, 
    int ls) {
  printf("Iteration %d:\n", k);
  printf("  fx = %f, x[0] = %f, x[1] = %f\n", fx, x[0], x[1]);
  printf("  xnorm = %f, gnorm = %f, step = %f\n", xnorm, gnorm, step);
  printf("\n");
  return 0;
}

double MaxentModel::compute_gradient(const vector<InstanceSet>& data,
    vector<double>* gradient) {
  gradient->resize(feature_weights.size(), 0.0);
  double objective = 0.0;
  MaxentInstance::const_iterator it;
  for (int i = 0; i < data.size(); ++i) {
    double log_prob = 0.0; // Unnormalized probability of this data point
    const MaxentInstance& true_instance = 
      data.at(i).instances.at(data.at(i).true_instance);
    for (it = true_instance.begin(); it != true_instance.end(); ++it) {
      int f_i = feature_index[it->first];
      (*gradient)[f_i] -= it->second;
      log_prob += it->second * feature_weights[f_i];
    }
    double z = 0.0; // normalizing constant
    vector<double> dot_products; // numerator of the probability of each instance
    for (int j = 0; j < data.at(i).instances.size(); ++j) {
      double dot_product = 0.0;
      const MaxentInstance& instance = data.at(i).instances[j];
      for (it = instance.begin(); it != instance.end(); ++it) {
        int f_i = feature_index[it->first];
        dot_product += it->second * feature_weights[f_i];
      }
      dot_product = exp(dot_product);
      z += dot_product;
      dot_products.push_back(dot_product);
    }
    for (int j = 0; j < data.at(i).instances.size(); ++j) {
      double prob = dot_products[j] / z;
      const MaxentInstance& instance = data.at(i).instances[j];
      for (it = instance.begin(); it != instance.end(); ++it) {
        int f_i = feature_index[it->first];
        (*gradient)[f_i] += it->second * prob;
      }
    }
    objective -= log_prob - log(z);
  }
  // Add the gradient for the L2 regularization
  if (l2_norm > 0.0) {
    for (int i = 0; i < feature_weights.size(); ++i) {
      objective += l2_norm * pow(feature_weights[i], 2);
      (*gradient)[i] += 2.0 * l2_norm * feature_weights[i];
    }
  }
  return objective;
}

double MaxentModel::compute_z(const InstanceSet& instance_set) {
  MaxentInstance::const_iterator it;
  double z = 0.0;
  for (int i = 0; i < instance_set.instances.size(); ++i) {
    double dot_product = 0.0;
    const MaxentInstance& instance = instance_set.instances[i];
    for (it = instance.begin(); it != instance.end(); ++it) {
      int f_i = feature_index[it->first];
      dot_product += it->second * feature_weights[f_i];
    }
    z += exp(dot_product);
  }
  return z;
}

const char* MaxentModel::error_name(int lbfgs_ret) {
  switch(lbfgs_ret) {
    case LBFGS_SUCCESS:
      return "L-BFGS reaches convergence."; break;
    case LBFGS_STOP:
      return "L-BFGS stops."; break;
    case LBFGS_ALREADY_MINIMIZED:
      return "The initial variables already minimize the objective function."; break;
    case LBFGSERR_UNKNOWNERROR:
      return "Unknown error."; break;
    case LBFGSERR_LOGICERROR:
      return "Logic error."; break;
    case LBFGSERR_OUTOFMEMORY:
      return "Insufficient memory."; break;
    case LBFGSERR_CANCELED:
      return "The minimization process has been canceled."; break;
    case LBFGSERR_INVALID_N:
      return "Invalid number of variables specified."; break;
    case LBFGSERR_INVALID_N_SSE:
      return "Invalid number of variables (for SSE) specified."; break;
    case LBFGSERR_INVALID_X_SSE:
      return "The array x must be aligned to 16 (for SSE)."; break;
    case LBFGSERR_INVALID_EPSILON:
      return "Invalid parameter lbfgs_parameter_t::epsilon specified."; break;
    case LBFGSERR_INVALID_TESTPERIOD:
      return "Invalid parameter lbfgs_parameter_t::past specified."; break;
    case LBFGSERR_INVALID_DELTA:
      return "Invalid parameter lbfgs_parameter_t::delta specified."; break;
    case LBFGSERR_INVALID_LINESEARCH:
      return "Invalid parameter lbfgs_parameter_t::linesearch specified."; break;
    case LBFGSERR_INVALID_MINSTEP:
      return "Invalid parameter lbfgs_parameter_t::max_step specified."; break;
    case LBFGSERR_INVALID_MAXSTEP:
      return "Invalid parameter lbfgs_parameter_t::max_step specified."; break;
    case LBFGSERR_INVALID_FTOL:
      return "Invalid parameter lbfgs_parameter_t::ftol specified."; break;
    case LBFGSERR_INVALID_WOLFE:
      return "Invalid parameter lbfgs_parameter_t::wolfe specified."; break;
    case LBFGSERR_INVALID_GTOL:
      return "Invalid parameter lbfgs_parameter_t::gtol specified."; break;
    case LBFGSERR_INVALID_XTOL:
      return "Invalid parameter lbfgs_parameter_t::xtol specified."; break;
    case LBFGSERR_INVALID_MAXLINESEARCH:
      return "Invalid parameter lbfgs_parameter_t::max_linesearch specified."; break;
    case LBFGSERR_INVALID_ORTHANTWISE:
      return "Invalid parameter lbfgs_parameter_t::orthantwise_c specified."; break;
    case LBFGSERR_INVALID_ORTHANTWISE_START:
      return "Invalid parameter lbfgs_parameter_t::orthantwise_start specified."; break;
    case LBFGSERR_INVALID_ORTHANTWISE_END:
      return "Invalid parameter lbfgs_parameter_t::orthantwise_end specified."; break;
    case LBFGSERR_OUTOFINTERVAL:
      return "The line-search step went out of the interval of uncertainty."; break;
    case LBFGSERR_INCORRECT_TMINMAX:
      return "A logic error occurred; alternatively, the interval of uncertainty became too small."; break;
    case LBFGSERR_ROUNDING_ERROR:
      return "A rounding error occurred; alternatively, no line-search step satisfies the sufficient decrease and curvature conditions."; break;
    case LBFGSERR_MINIMUMSTEP:
      return "The line-search step became smaller than lbfgs_parameter_t::min_step."; break;
    case LBFGSERR_MAXIMUMSTEP:
      return "The line-search step became larger than lbfgs_parameter_t::max_step."; break;
    case LBFGSERR_MAXIMUMLINESEARCH:
      return "The line-search routine reaches the maximum number of evaluations."; break;
    case LBFGSERR_MAXIMUMITERATION:
      return "The algorithm routine reaches the maximum number of iterations."; break;
    case LBFGSERR_WIDTHTOOSMALL:
      return "Relative width of the interval of uncertainty is at most lbfgs_parameter_t::xtol."; break;
    case LBFGSERR_INVALIDPARAMETERS:
      return "A logic error (negative line-search step) occurred."; break;
    case LBFGSERR_INCREASEGRADIENT:
      return "The current search direction increases the objective function value."; break;
  }
  return "?";
}
