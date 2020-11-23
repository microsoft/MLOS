# This is a simple Makefile used mostly for local interactive development.

CONFIGURATION ?= Release

all: dotnet-build

clean: dotnet-clean
	rm -rf ../.nuget/packages/mlos.* || true
	rm -rf ../Mlos.CodeGen.out/ExternalIntegrationExample

distclean: clean
	rm -rf ./bin/
	rm -rf ./obj/
	rm -rf ../.nuget/
	rm -rf ../Mlos.CodeGen.out/

dotnet-build:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) /p:PackMlosDependencies=true

dotnet-build-quick:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) --no-restore

# A convenience helper for local package development:
dotnet-rebuild-all:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) /p:PackMlosDependencies=true /p:CleanMlosPackages=true

dotnet-clean:
	dotnet build $(MSBUILD_ARGS) -c $(CONFIGURATION) --no-restore /t:clean 2>/dev/null >/dev/null || true

# A quick wrapper for invoking testing the CMakeLists.txt wrapper.
cmake-build:
	mkdir -p ../build
	cd ../build/ && cmake ..
	cd ../build/ && make -j ExternalIntegrationExample.SettingsRegistry
