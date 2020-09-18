# Provides targets that are a wrapper around our CMake and Makefiles so
# we can easily run "make" in a given source directory.
# Expects the variable RelativePathToProjectRoot (e.g. ..) to be set prior to include.
# To allow combining with other rules, this one doesn't define the all/clean targets.
# They should be defined to depend on the dotnet-build/dotnet-clean targets
# *before* including this file.

ifeq ($(RelativePathToProjectRoot),)
    $(error Makefile authoring error: RelativePathToProjectRoot is not set.)
endif
ifeq ($(RelativePathToProjectRoot),.)
    $(error Makefile authoring error: CMakeWrapper.mk should not be included in the root Makefile.)
endif

ifneq ($(MlosCommonMkImported),true)
    include $(RelativePathToProjectRoot)/build/Common.mk
endif

RelativeSourceDir := $(shell realpath --relative-to $(RelativePathToProjectRoot) .)

ConfigurationBuildDir := $(CmakeBuildDir)/$(CONFIGURATION)/$(RelativeSourceDir)
ConfigurationMakefile := $(ConfigurationBuildDir)/Makefile

handledtargets += cmake-build cmake-install cmake-test cmake-clean \
		  cmake-buildfiles clean-cmake-buildfiles \
		  local-cmake-distclean $(ConfigurationMakefile)

# To be added the to the including Makefile's all target.
.PHONY: cmake-build
cmake-build: $(ConfigurationMakefile)
	$(MAKE) -C $(ConfigurationBuildDir)
	@ echo "make cmake-build target finished."

# To be added the to the including Makefile's install target.
.PHONY: cmake-install
cmake-install: $(ConfigurationMakefile)
	$(MAKE) -C $(ConfigurationBuildDir) install
	@ echo "make cmake-install target finished."

# To be added the to the including Makefile's test target.
.PHONY: cmake-test
cmake-test: $(ConfigurationMakefile)
	$(MAKE) -C $(ConfigurationBuildDir) test
	@ echo "make cmake-test target finished."

# To be added the to the including Makefile's clean target.
.PHONY: cmake-clean
cmake-clean: $(ConfigurationMakefile)
	$(MAKE) -C $(ConfigurationBuildDir) clean

.PHONY: cmake-buildfiles
.NOTPARALLEL: cmake-buildfiles
cmake-buildfiles:
	@ $(MAKE) -C $(MLOS_ROOT) cmake-buildfiles

.PHONY: clean-cmake-buildfiles
clean-cmake-buildfiles:
	 @ $(RM) $(ConfigurationBuildDir)/CMakeCache.txt
	 @ $(RM) $(ConfigurationMakefile)

# Call the repo root Makefile to build the CMake Makefile
.NOTPARALLEL: $(ConfigurationMakefile)
$(ConfigurationMakefile):
	@ $(MAKE) cmake-buildfiles

# Cleanup the outputs produced by a mistaken in-tree cmake.
# Most IDEs will dump those files into a local build/ directory.
# To be added to the including Makefile's distclean target.
.PHONY: local-cmake-distclean
local-cmake-distclean:
	@- $(RM) ./build/Makefile
	@- $(RM) ./build/*.ninja
	@- $(RM) ./build/CMake*
	@- $(RM) ./build/cmake.*
	@- $(RM) ./build/*.cmake
	@- $(RM) ./build/*.json
	@- $(RM) ./build/*.txt
	@- $(RM) ./CMakeFiles
	@- $(RM) ./CMakeCache.txt
	@- $(RM) ./build

# Send all other targets to the project specific Makefile produced by cmake.
# NOTE: Because of this, this file should be included last.
unhandledtargets := $(filter-out $(handledtargets),$(MAKECMDGOALS))
ifneq ($(unhandledtargets),)
$(unhandledtargets): $(ConfigurationMakefile)
	$(MAKE) -C $(ConfigurationBuildDir) $(unhandledtargets)
endif
