CXX ?= c++
CPPFLAGS += -Iinclude
# Компактный CLOSED для MeshA* (только initial-клетки, следствие леммы 1). Выключить: make COMPACT_CLOSED=0
COMPACT_CLOSED ?= 1
ifeq ($(COMPACT_CLOSED),1)
CPPFLAGS += -DCOMPACT_CLOSED
endif
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

test: mesh_astar
	bash research/gluing/test.sh

clean:
	rm -rf obj mesh_astar
