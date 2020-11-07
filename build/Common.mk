# Some common variables/rules for our different Makefile wrappers.

ifeq ($(RelativePathToProjectRoot),)
    $(error RelativePathToProjectRoot not set.)
endif

ifeq ($(MlosCommonMkImported),true)
    $(error Common.mk has already been included.)
endif

# Enable parallel builds by default.
# To disable, run "make -j1".
NumProcs := $(shell nproc)
MAKEFLAGS := -j -l$(NumProcs) $(MAKEFLAGS)

SHELL	:= /bin/bash
RM	:= rm -rf
MKDIR	:= mkdir -p

# We currently depend on clang due to use of __declspec(selectany) and other
# attributes in the codegen output.
CC	:= clang-10
CXX	:= clang++-10
export CC
export CXX

MLOS_ROOT := $(shell realpath $(RelativePathToProjectRoot))
RelativeSourceDir := $(shell realpath --relative-to $(RelativePathToProjectRoot) $(CURDIR))
ifeq ($(RelativeSourceDir),.)
    RelativeSourceDir :=
endif

# We place our cmake output files in a different directory than usual, since we
# keep msbuild props/targets files in build/
CmakeBuildDir := $(MLOS_ROOT)/out/cmake

CMAKE := cmake
DOTNET := dotnet

# Make sure to check the usual pip install location for commands.
PATH := $(PATH):${HOME}/.local/bin
export PATH

# Make dotnet be a little less noisy.
DOTNET_SKIP_FIRST_TIME_EXPERIENCE := 1
DOTNET_CLI_TELEMETRY_OPTOUT := 1
export DOTNET_CLI_TELEMETRY_OPTOUT
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE

# Recognized configurations.
SupportedConfigurations := Release Debug
DefaultConfiguration := Release

# Read selected CONFIGURATION from an environment variable.
# e.g. # CONFIGURATION=Debug make
CONFIGURATION := ${CONFIGURATION}

# If not set, set a default configuration.
ifeq ($(CONFIGURATION),)
    $(info CONFIGURATION not specified.  Defaulting to $(DefaultConfiguration))
    CONFIGURATION = $(DefaultConfiguration)
endif
# Change case as a convenience.
ifeq ($(CONFIGURATION),release)
    CONFIGURATION = Release
else ifeq ($(CONFIGURATION),debug)
    CONFIGURATION = Debug
endif
# Export it so we don't need to set it again.
export CONFIGURATION

# Check that the provided configuration is one that we support.
ifeq ($(filter $(CONFIGURATION),$(SupportedConfigurations)),)
    $(error CONFIGURATION=$(CONFIGURATION) is not a supported configuration: $(SupportedConfigurations))
endif

# Variables tracking additional targets to be added to by later Makefile wrappers.
handledtargets = all test check install clean distclean rebuild ctags

# Mark this file as imported.
MlosCommonMkImported := true
