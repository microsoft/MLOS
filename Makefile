# -----------------------------------------------------------------------------
# CMake project wrapper Makefile
# This allows us to simply run "make" in various source dirs.
# We support targetting Debug vs. Release configurations using the
# CONFIGURATION environment variable.
# See Also: https://stackoverflow.com/a/29678916/10772564
# -----------------------------------------------------------------------------

RelativePathToProjectRoot := .
include ./build/Common.mk

handledtargets += cmake-build cmake-install cmake-test cmake-check \
		  cmake-buildfiles clean-cmake-buildfiles \
		  cmake-clean cmake-distclean \
		  python-checks python-test python-clean \
		  website website-clean \
		  grpc-clean mlos-codegen-clean \
		  docker-image

# Build using dotnet and the Makefile produced by cmake.
.PHONY: all
all: dotnet-build cmake-build python-checks
	@ echo "make all target finished."

.PHONY: test
test: dotnet-test cmake-test python-test
	@ echo "make test target finished."

.PHONY: check
check: all test

.PHONY: install
install: dotnet-install cmake-install
	@ echo "make install target finished."

.PHONY: clean
clean: cmake-clean dotnet-clean grpc-clean mlos-codegen-clean website-clean python-clean

.PHONY: distclean
distclean: clean cmake-distclean

.PHONY: rebuild
rebuild: clean all

# Somewhat overkill clean rules - they just nuke the top-level output directories.

.PHONY: mlos-codegen-clean
mlos-codegen-clean: dotnet-clean
	@ $(RM) $(MLOS_ROOT)/Mlos.CodeGen.out

.PHONY: grpc-clean
grpc-clean:
	@ $(RM) $(MLOS_ROOT)/Grpc.out

.PHONY: website
website:
	$(MAKE) -C website

.PHONY: website-clean
website-clean:
	$(MAKE) -C website clean

.PHONY: python-clean
python-clean:
	@ find $(MLOS_ROOT)/source/Mlos.Python/ -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf
	@ find $(MLOS_ROOT)/source/Mlos.Python/ -type f -name '*.pyc' -print0 | xargs -0 -r rm -f
	@ $(RM) $(MLOS_ROOT)/source/Mlos.Python/mlos.egg-info

# Build the dirs.proj file in this directory with "dotnet build"
include $(MLOS_ROOT)/build/DotnetWrapperRules.mk

# For the rest, the top-level CMakeLists.txt is special,
# so we don't use the CMakeWrapperRules.mk file.

ConfigurationCmakeDir := $(CmakeBuildDir)/$(CONFIGURATION)
ConfigurationMakefile := $(ConfigurationCmakeDir)/Makefile
CmakeGenerator := "Unix Makefiles"

handledtargets += $(ConfigurationMakefile)

.PHONY: cmake-build
cmake-build: $(ConfigurationMakefile)
	@  $(MAKE) -C $(ConfigurationCmakeDir)
	@ echo "make cmake-build target finished."

.PHONY: cmake-install
cmake-install: $(ConfigurationMakefile)
	@  $(MAKE) -C $(ConfigurationCmakeDir) install
	@ echo "make cmake-install target finished."

.PHONY: cmake-test
cmake-test: $(ConfigurationMakefile)
	@  $(MAKE) -C $(ConfigurationCmakeDir) test
	@ echo "make cmake-test target finished."

.PHONY: cmake-check
cmake-check:
	@  $(MAKE) -C $(ConfigurationCmakeDir) check
	@ echo "make cmake-check target finished."

.NOTPARALLEL: cmake-clean
.PHONY: cmake-clean
cmake-clean:
	@- $(MAKE) -C $(MLOS_ROOT) $(ConfigurationMakefile) || true
	@- $(MAKE) -C $(ConfigurationCmakeDir) clean || true

.PHONY: cmake-buildfiles
cmake-buildfiles: $(ConfigurationMakefile)

# Create the build Makefile using cmake.
.NOTPARALLEL: $(ConfigurationMakefile)
.PHONY: $(ConfigurationMakefile)
$(ConfigurationMakefile): CMakeLists.txt
	@  $(MKDIR) $(ConfigurationCmakeDir) > /dev/null
	@  $(CMAKE) -D CMAKE_BUILD_TYPE=$(CONFIGURATION) -S $(MLOS_ROOT) -B $(ConfigurationCmakeDir) -G $(CmakeGenerator)

.PHONY: clean-cmake-buildfiles
clean-cmake-buildfiles:
	@ $(RM) $(ConfigurationCmakeDir)/CMakeCache.txt
	@ $(RM) $(ConfigurationCmakeDir)/_deps
	@ $(RM) $(ConfigurationMakefile)

.PHONY: python-checks
python-checks:
	@ ./scripts/run-python-checks.sh
	@ echo "make python-checks target finished."

.PHONY: python-test
python-test:
	@ ./scripts/run-python-tests.sh
	@ echo "make python-test target finished."

# Don't force cmake regen every time we run ctags - only if it doesn't exist
.PHONY: ctags
ctags:
	@  test -e $(ConfigurationMakefile) || $(MAKE) -C . $(ConfigurationMakefile)
	@  $(MAKE) -C $(ConfigurationCmakeDir) ctags

# Provide a target to help build a local docker image.
#
UbuntuVersion := ${UbuntuVersion}
ifeq ($(UbuntuVersion),)
    UbuntuVersion = 20.04
endif
ValidUbuntuVersions := 16.04 18.04 20.04
ifneq ($(filter-out $(ValidUbuntuVersions),$(UbuntuVersion)),)
    $(error Unhandled UbuntuVersion: $(UbuntuVersion))
endif
MlosBuildBaseArg := ${MlosBuildBaseArg}
ifeq ($(MlosBuildBaseArg),)
    MlosBuildBaseArg = without-extras
endif
ValidMlosBuildBaseArgs := without-extras with-extras
ifneq ($(filter-out $(ValidMlosBuildBaseArgs),$(MlosBuildBaseArg)),)
    $(error Unhandled MlosBuildBaseArg: $(MlosBuildBaseArg))
endif
MlosBuildImageTarget := ${MlosBuildImageTarget}
ifeq ($(MlosBuildImageTarget),)
    MlosBuildImageTarget = mlos-build-base-$(MlosBuildBaseArg)
endif
ValidMlosBuildImageTargets := mlos-build-base-with-source mlos-build-base-with-extras mlos-build-base-without-extras mlos-build-base-with-python
ifneq ($(filter-out $(ValidMlosBuildImageTargets),$(MlosBuildImageTarget)),)
    $(error Unhandled MlosBuildImageTarget: $(MlosBuildImageTarget))
endif
.PHONY: docker-image
docker-image:
	docker pull ghcr.io/microsoft-cisl/mlos/mlos-build-ubuntu-$(UbuntuVersion):latest
	docker build . --target $(MlosBuildImageTarget) \
	    --build-arg=MlosBuildBaseArg=$(MlosBuildBaseArg) \
	    --build-arg=UbuntuVersion=$(UbuntuVersion) \
	    --build-arg=http_proxy=${http_proxy} \
	    -t mlos-build-ubuntu-$(UbuntuVersion)
	@ echo Finished building mlos-build-ubuntu-$(UbuntuVersion) image.
	@ echo Run "docker run -v $$PWD:/src/MLOS --name mlos-build mlos-build-ubuntu-$(UbuntuVersion)" to start an instance.

# Cleanup the outputs produced by cmake.
.PHONY: cmake-distclean
cmake-distclean: cmake-clean
	@- $(RM) $(ConfigurationCmakeDir)/Makefile
	@- $(RM) $(ConfigurationCmakeDir)/*.ninja
	@- $(RM) $(ConfigurationCmakeDir)/_deps
	@- $(RM) $(ConfigurationCmakeDir)/source
	@- $(RM) $(ConfigurationCmakeDir)/test
	@- $(RM) $(ConfigurationCmakeDir)/CMake*
	@- $(RM) $(ConfigurationCmakeDir)/cmake.*
	@- $(RM) $(ConfigurationCmakeDir)/*.cmake
	@- $(RM) $(ConfigurationCmakeDir)/*.json
	@- $(RM) $(ConfigurationCmakeDir)/*.txt

# Send all other targets to the Makefile produced by cmake.
unhandledtargets := $(filter-out $(handledtargets),$(MAKECMDGOALS))
ifneq ($(unhandledtargets),)
$(unhandledtargets): $(ConfigurationMakefile)
	@ $(MAKE) -C $(ConfigurationCmakeDir) $(unhandledtargets)
endif
