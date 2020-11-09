all: dotnet-build

clean: dotnet-clean

dotnet-build:
	dotnet build /p:PackMlosDependencies=true

dotnet-build-quick:
	dotnet build --no-restore

dotnet-rebuild-all:
	dotnet build /p:PackMlosDependencies=true /p:CleanMlosPackages=true

dotnet-clean:
	dotnet build --no-restore /t:clean
