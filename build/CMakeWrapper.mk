# Provides targets that wrap cmake commands to allow for simply running "make"
# or "CONFIGURATION=Debug make" in the current directory on Linux machines.
# Expects the variable RelativePathToProjectRoot (e.g. ..) to be set prior to include.

.PHONY: all
all: cmake-build # ctags
	@ echo "make all target finished."

.PHONY: install
install: cmake-install

.PHONY: clean
clean: cmake-clean

.PHONY: distclean
distclean: clean local-cmake-distclean

.PHONY: test
test: cmake-test
	@ echo "make test target finished."

include $(RelativePathToProjectRoot)/build/CMakeWrapperRules.mk
include $(RelativePathToProjectRoot)/build/CommonRules.mk
