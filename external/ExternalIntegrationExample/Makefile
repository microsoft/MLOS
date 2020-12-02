# A very simple make file to separate the rest of the source tree of our example from its build outputs.

CONFIGURATION ?= Release

all: cmake-build

cmake-build:
	mkdir -p ./build
	cd ./build/ && cmake ..
	cd ./build/ && make -j

test: cmake-build
	# Run the test program.
	./build/ExternalIntegrationExample

clean:
	make -C ExternalIntegrationExample.SettingsRegistry/ clean
	cd ./build/ 2>/dev/null && make clean 2>/dev/null || true

distclean: clean
	make -C ExternalIntegrationExample.SettingsRegistry/ distclean
	rm -rf ./build/
