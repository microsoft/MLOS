# Provides targets that wrap cmake commands to allow for simply running "make"
# or "CONFIGURATION=Debug make" in the current directory on Linux machines.
# Expects the variable RelativePathToProjectRoot (e.g. ..) to be set prior to include.

.PHONY: all
all: dotnet-build # ctags
	@ echo "make all target finished."

.PHONY: install
install: dotnet-install
	@ echo "make install target finished."

.PHONY: clean
clean: dotnet-clean

.PHONY: distclean
distclean: clean

.PHONY: test
test: dotnet-test
	@ echo "make test target finished."

include $(RelativePathToProjectRoot)/build/DotnetWrapperRules.mk
include $(RelativePathToProjectRoot)/build/CommonRules.mk
