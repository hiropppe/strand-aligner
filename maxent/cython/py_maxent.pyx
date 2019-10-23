# distutils: language = c++
# distutils: sources = cpp/maxent/maxent.cpp
# distutils: include_dirs = .
# distutils: libraries = lbfgs

from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp.utility cimport pair

cdef extern from "cpp/maxent/maxent.h":
  ctypedef vector[pair[string, double] ] MaxentInstance
  cdef cppclass InstanceSet:
    vector[MaxentInstance] instances
    int true_instance
  cdef cppclass MaxentModel:
    MaxentModel(double l2) except+

    void set_training_data(vector[InstanceSet]*)
    int lbfgs_train()
    void init_feature_weights(vector[InstanceSet]&)
    double get_prob(InstanceSet&, int)
    void get_probs(InstanceSet&, vector[double]*)
    int get_label(InstanceSet&)
    double test(vector[InstanceSet])
    void get_features(vector[pair[string, double] ]*)

cdef class PyMaxent:
  cdef MaxentModel* thisptr
  def __cinit__(self, l2_norm):
    cdef double l2 = l2_norm
    self.thisptr = new MaxentModel(l2)
  def __dealloc__(self):
    del self.thisptr

  # The training data should be a list of lists of tuples, each of which are
  # (string, double) pairs.
  def set_training_data(self, py_data):
    cdef vector[InstanceSet]* cpp_data = self.convert_instance_sets(py_data)
    self.thisptr.set_training_data(cpp_data)

  def lbfgs_train(self):
    return self.thisptr.lbfgs_train()

  # Get the probability of the instance at the given index
  def get_prob(self, py_instance_set, index):
    cdef InstanceSet* cpp_instance_set = self.convert_instance_set(py_instance_set)
    result = self.thisptr.get_prob(cpp_instance_set[0], index)
    del cpp_instance_set
    return result

  # Returns the probabilities for all instances in the set
  def get_probs(self, py_instance_set):
    cdef vector[double] cpp_result
    cdef InstanceSet* cpp_instance_set = self.convert_instance_set(py_instance_set)
    self.thisptr.get_probs(cpp_instance_set[0], &cpp_result)
    del cpp_instance_set
    result = []
    for prob in cpp_result:
      result.append(prob)
    return result

  def get_label(self, py_instance_set):
    cdef InstanceSet* cpp_instance_set = self.convert_instance_set(py_instance_set)
    result = self.thisptr.get_label(cpp_instance_set[0])
    del cpp_instance_set
    return result

  def test(self, py_data):
    cdef vector[InstanceSet]* cpp_data = self.convert_instance_sets(py_data)
    result = self.thisptr.test(cpp_data[0])
    del cpp_data
    return result

  # Returns the feature names/weights as a list of tuples
  def get_features(self):
    cdef vector[pair[string, double] ] features
    self.thisptr.get_features(&features)
    result = []
    for i in xrange(0, features.size()):
      result.append((features[i].first, features[i].second))
    return result

  # This allocates a new object which must be deleted.
  cdef vector[InstanceSet]* convert_instance_sets(self, py_data):
    cdef vector[InstanceSet]* cpp_data = new vector[InstanceSet]()
    cdef InstanceSet cpp_instance_set
    cdef MaxentInstance cpp_instance
    for instance_set in py_data:
      cpp_instance_set.instances.clear()
      cpp_instance_set.true_instance = instance_set.true_instance
      for instance in instance_set.instances:
        cpp_instance.clear()
        for (name, value) in instance:
          cpp_instance.push_back(pair[string, double](name, value))
        cpp_instance_set.instances.push_back(cpp_instance)
      cpp_data.push_back(cpp_instance_set)
    return cpp_data

  # This allocates a new object which must be deleted.
  cdef InstanceSet* convert_instance_set(self, py_instance_set):
    cdef InstanceSet* cpp_instance_set = new InstanceSet()
    cdef MaxentInstance cpp_instance
    cpp_instance_set.true_instance = py_instance_set.true_instance
    for instance in py_instance_set.instances:
      cpp_instance.clear()
      for (name, value) in instance:
        cpp_instance.push_back(pair[string, double](name, value))
      cpp_instance_set.instances.push_back(cpp_instance)
    return cpp_instance_set

class PyInstanceSet:
  def __init__(self):
    self.instances = []
    self.true_instance = -1
