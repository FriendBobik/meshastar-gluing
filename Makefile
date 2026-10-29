CXX ?= c++
CPPFLAGS += -Iinclude
CXXFLAGS ?= -std=c++17 -O3 -Wall -Wextra
LDFLAGS ?=

SOURCES := $(wildcard src/*.cpp)
OBJECTS := $(patsubst src/%.cpp,obj/%.o,$(SOURCES))
DEPS := $(OBJECTS:.o=.d)

.PHONY: all clean test
all: mesh_astar

mesh_astar: $(OBJECTS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $^ -o $@

obj/%.o: src/%.cpp
	@mkdir -p $(@D)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c $< -o $@

-include $(DEPS)

test:
	bash research/gluing/test.sh

clean:
	rm -rf obj mesh_astar
