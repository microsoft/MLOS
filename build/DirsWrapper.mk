# Provides targets that simulate "msbuild dirs.proj" for recursively building
# the current directory on Linux machines by simply running "make" or
# "CONFIGURATION=Debug make".
# Expects the variable RelativePathToProjectRoot (e.g. ..) to be set prior to include.

.PHONY: all
all: dotnet-build cmake-build # ctags
	@ echo "make all target finished."

.PHONY: install
install: dotnet-install cmake-install
	@ echo "make install target finished."

.PHONY: clean
clean: dotnet-clean cmake-clean

.PHONY: distclean
distclean: clean local-cmake-distclean

.PHONY: test
test: dotnet-test cmake-test
	@ echo "make test target finished."

include $(RelativePathToProjectRoot)/build/DotnetWrapperRules.mk
include $(RelativePathToProjectRoot)/build/CMakeWrapperRules.mk
include $(RelativePathToProjectRoot)/build/CommonRules.mk
