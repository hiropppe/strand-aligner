ifdef DEBUG
OPT=-g
else
OPT=-O3 -ffast-math -funroll-loops -DNDEBUG #-mtune=native -march=native
endif

ifdef PROF
OPTS=-pg $(OPT) #-fno-inline $(OPT)
else
OPTS=$(OPT)
endif

BOOST_ROOT = /usr/include/boost

INCS = -I. -I$(BOOST_ROOT)
LIBS = -L$(BOOST_ROOT)/stage/lib
LDFLAGS = -lm -llbfgs -lboost_program_options

CXX = /usr/bin/g++

CXXFLAGS=$(OPTS) $(INCS)

SRC_FILES = \
  cpp/util/math_util.cpp \
  cpp/maxent/maxent.cpp
MAIN_FILE = cpp/main.cpp

OBJ_FILES = $(SRC_FILES:%.cpp=%.o)
MAIN_OBJ = $(MAIN_FILE:%.cpp=%.o)
MAIN_TARGET = cpp/lbfgs_test

%.o: %.cpp %.h
	$(CXX) $(CXXFLAGS) -o $@ -c $<

all: $(OBJ_FILES) $(MAIN_OBJ)
	$(CXX) $(CXXFLAGS) $(LIBS) $(OBJ_FILES) $(MAIN_OBJ) -o $(MAIN_TARGET) $(LDFLAGS)

clean:
	rm $(OBJ_FILES) $(MAIN_OBJ) $(MAIN_TARGET)
