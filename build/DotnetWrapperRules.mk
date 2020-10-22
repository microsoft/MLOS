# Provides targets that are a wrapper around "dotnet build" for our .csproj so
# we can easily run "make" in a given source directory.
# Expects the variable RelativePathToProjectRoot (e.g. ..) to be set prior to include.
# To allow combining with other rules, this one doesn't define the all/clean targets.
# They should be defined to depend on the dotnet-build/dotnet-clean targets
# *before* including this file.

ifeq ($(RelativePathToProjectRoot),)
    $(error Makefile authoring error: RelativePathToProjectRoot is not set)
endif

ifneq ($(MlosCommonMkImported),true)
    include $(RelativePathToProjectRoot)/build/Common.mk
endif

# Determine (roughly) where the outputs should be (per the msbuild files).
# Needed for "clean" target.
# See Also: Mlos.Common.props
DotnetBaseOutDir := $(MLOS_ROOT)/out/dotnet
DotnetOutputPath := $(DotnetBaseOutDir)/$(RelativeSourceDir)

# Find all the *.csproj, dirs.proj files in this directory and make some
# corresponding fake targets for the "all" target to depend on.
Csprojs := $(wildcard *.csproj)
CsprojBuildTargets := $(Csprojs:.csproj=.csproj.fake-build-target)
CsprojBuildQuickTargets := $(Csprojs:.csproj=.csproj.fake-build-quick-target)
CsprojTestTargets := $(Csprojs:.csproj=.csproj.fake-test-target)
DirsProj := $(wildcard dirs.proj)
DirsProjBuildTarget := $(DirsProj:.proj=.proj.fake-build-target)
DirsProjTestTarget := $(DirsProj:.proj=.proj.fake-test-target)

# To be added to the including Makefile's all target.
.PHONY: dotnet-build
dotnet-build: $(CsprojBuildTargets) $(DirsProjBuildTarget)
	@ echo "make dotnet-build target finished."

# A target for quickly rebuilding just a given project and none of its dependencies.
# Note: this doesn't make sense to use with dirs.proj, so we skip it here.
.PHONY: dotnet-build-quick
dotnet-build-quick: $(CsprojBuildQuickTargets)
	@ echo "make dotnet-build-quick target finished."

.PHONY: dotnet-test
dotnet-test: $(CsprojTestTargets) $(DirsProjTestTarget)
	@ echo "make dotnet-test target finished."

.PHONY: dotnet-install
dotnet-install:
	@ echo "make dotnet-install is currently a no-op."

# For each of the fake build targets, just call "dotnet build" on its
# corresponding *.csproj file
# We won't track any inputs/outputs/dependencies - we just let "dotnet build" handle that.
# Additionally, we let it handle the output directory via the .csproj file (see above).
%.fake-build-target:
	@ # Note: This command currently also does a "dotnet restore" first,
	@ # which can be slow, however is difficult to check when it is unnecessary.
	@ # Note: -m tells it to build in parallel.
	@ $(DOTNET) build -m --configuration $(CONFIGURATION) $(@:.fake-build-target=)

%.fake-build-quick-target:
	@ # A target to allow quickly rebuilding just a given project and none of its dependencies.
	@ $(DOTNET) build -m --configuration $(CONFIGURATION) --no-restore /p:BuildProjectReferences=false $(@:.fake-build-quick-target=)

# By default don't run certain tests.
# To override, run with:
#   DOTNET_TEST_FILTER=' ' make dotnet-test
DOTNET_TEST_FILTER := ${DOTNET_TEST_FILTER}
ifeq ($(DOTNET_TEST_FILTER),)
    DOTNET_TEST_FILTER = --filter='Category!=SkipForCI'
endif

# For each of the fake test targets, just call "dotnet test" on its
# corresponding *.csproj file
# For now, don't force a rebuild first.
%.fake-test-target: #%.fake-build-target
	$(DOTNET) test --no-build -m --configuration $(CONFIGURATION) $(DOTNET_TEST_FILTER) $(@:.fake-test-target=)

# Note: this clean method somewhat lazily removes both Debug and Release build outputs.
# To be added to the including Makefile's clean target.
.PHONY: dotnet-clean
dotnet-clean:
	@ $(RM) $(DotnetOutputPath)

handledtargets += $(Csprojs) $(CsProjBuildTargets) $(CsProjTestTargets) \
    $(DirsProj) $(DirsProjBuildTarget) $(DirsProjTestTarget) \
    dotnet-build dotnet-build-quick dotnet-install dotnet-test dotnet-clean
