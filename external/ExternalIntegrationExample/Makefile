# A very simple make file to separate the rest of the source tree of our example from its build outputs.

all: cmake-build

cmake-build:
	mkdir -p build
	cd build && cmake ..
	cd build && make -j
