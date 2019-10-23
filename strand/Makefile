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

INCS = -I. -I$(BOOST_ROOT)
LIBS = -L$(BOOST_ROOT)/stage/lib
LDFLAGS = -lm -lpthread -ldl -lboost_program_options -lboost_filesystem -lboost_serialization -lpthread -lboost_thread -lboost_system

CXX = /usr/bin/g++

CXXFLAGS=$(OPTS) $(INCS)

SRC_FILES = \
	aligner.cpp \
  gale_church_aligner.cpp
MAIN_FILE = main.cpp

OBJ_FILES = $(SRC_FILES:%.cpp=%.o)
MAIN_OBJ = $(MAIN_FILE:%.cpp=%.o)
MAIN_TARGET = aligner_test

%.o: %.cpp %.h
	$(CXX) $(CXXFLAGS) -o $@ -c $<

all: $(OBJ_FILES) $(MAIN_OBJ)
	$(CXX) $(CXXFLAGS) $(LIBS) $(OBJ_FILES) $(MAIN_OBJ) -o $(MAIN_TARGET) $(LDFLAGS)

clean:
	rm $(OBJ_FILES) $(MAIN_OBJ) $(MAIN_TARGET)
