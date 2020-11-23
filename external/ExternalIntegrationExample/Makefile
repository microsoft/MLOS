# A very simple make file to separate the rest of the source tree of our example from its build outputs.

all: cmake-build

cmake-build:
	mkdir -p ./build
	cd ./build/ && cmake ..
	cd ./build/ && make -j

test: cmake-build
	# Check for pre-existing shared memory remnants.
	../../build/CMakeHelpers/CheckForMlosSharedMemories.sh
	# Run the test program.
	./build/ExternalIntegrationExample
	# Make sure to cleanup after ourselves.
	../../build/CMakeHelpers/RemoveMlosSharedMemories.sh

clean:
	make -C ExternalIntegrationExample.SettingsRegistry/ clean
	cd ./build/ && make clean || true

distclean: clean
	make -C ExternalIntegrationExample.SettingsRegistry/ distclean
	rm -rf ./build/
