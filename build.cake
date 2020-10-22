#tool nuget:?package=NUnit.ConsoleRunner&version=3.4.0
#tool nuget:?package=nuget.commandline&version=5.3.0
#addin nuget:?package=Cake.CMake&version=1.2.0
#addin nuget:?package=Cake.Docker&version=0.10.0

using System.Diagnostics;
using System.Reflection;
using IO = System.IO;

//
// ARGUMENTS
//
var Target = Argument("target", "Default");
var Configuration = Argument("configuration", "Release");
string AnyCPUPlatform = "AnyCPU";

string ObjectDirectory
{
    get
    {
        string objectDirectory =  Configuration switch
        {
                "Release" => objectDirectory = "obj",
                "Debug" => objectDirectory = "objd",
                _ => throw new InvalidOperationException("Unsupported configuration")
        };

        return objectDirectory;
    }
}

var MsBuildSettings = new DotNetCoreMSBuildSettings { MaxCpuCount = 0 };

//
// PREPARATION
//

var DockerImageName = "mssql-server-linux-with-mlos-python";
var SqlPassword = GenerateRandomPassword(length: 10);

// Define directories and files paths.
//

// Output directory contains build results.
//
var OutputDir = Directory("./out/");

// Output directory for cmake.
// See Also: Makefile, build/Common.mk
//
var CMakeConfiguration = Configuration;
var CMakeBuildDir = Directory($"./out/cmake/{CMakeConfiguration}");

// Docker Test Directory contains the generated dockerfiles and connection string files
// required for E2E Docker tests
//
var OriginalDockerfileFilePath = "./source/Mlos.Python/Docker/Dockerfile";
var DockerTestDirectory = Directory("./source/Mlos.Python/temp");
var TestDockerfileFilePath = IO.Path.Combine(DockerTestDirectory, "testdockerfile");

// We produce all the build artifacts in the target directory.
// - nuget package with Mlos sources
//
var TargetDir = Directory("./target/");
var SolutionFilePath = "./source/Mlos.NetCore.sln";

// MSBuild projects
//
string[] MSBuildProjectsFilePaths = new string[]
{
    "./source/Examples/SmartCache/SmartCache.vcxproj",
    "./source/Examples/SmartSharedChannel/SmartSharedChannel.vcxproj",
};

// Define NetCore test projects.
//
string[] NetCoreTestProjectsFilePaths = new string[]
{
//    "./source/Mlos.Model.Services.UnitTests/Mlos.Model.Services.UnitTests.csproj",
    "./source/Mlos.NetCore.UnitTest/Mlos.NetCore.UnitTest.csproj",
};

// Define MSBuild test projects.
//
string[] TestProjectsFilePaths = new string[]
{
    "./test/Mlos.TestRun/Mlos.TestRun.proj",
};

//
// Helper functions.
//

// Generate a mostly random password. Note that the first three characters of any password for now
// will be "Aa0" and thus the minimum password length is 3.
//
string GenerateRandomPassword(int length)
{
    if (length <= 3)
    {
        throw new ArgumentException("The minimum length of a generated password is 3.");
    }

    const string validCharacters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890";
    StringBuilder passwordBuilder = new StringBuilder();

    // Make sure to include all required character classes
    //
    passwordBuilder.Append("Aa0");

    Random random = new Random();
    for (int i = 3; i < length; i++)
    {
        passwordBuilder.Append(validCharacters[random.Next(validCharacters.Length)]);
    }

    return passwordBuilder.ToString();
}

// Gets the filepath to the build output for the given project.
//
string GetBuildOutputFilePath(string projectPath, string fileName)
{
    const string outputRootPath = "./out/obj/";

    string filePath = IO.Path.Combine(outputRootPath, projectPath, ObjectDirectory, "amd64", fileName);

    if (!IO.File.Exists(filePath))
    {
        throw new InvalidOperationException($"Unable to locate file {fileName} for project {projectPath}. Unable to locate {filePath}.");
    }

    return filePath;
}

//
// TASKS
//
Task("Precheck")
    .Does(() =>
    {
        // Ensure we are not running as CoreXT.
        //
        if ((EnvironmentVariable("BUILD_COREXT") ?? string.Empty) == "1")
        {
            Information("CoreXT is not supported");
            throw new InvalidOperationException("CoreXT is not supported");
        }

        Information(string.Format("UncrustifyAutoFix: '{0}'", EnvironmentVariable("UncrustifyAutoFix") ?? string.Empty));
    });

Task("Clean")
    .IsDependentOn("Precheck")
    .Does(() =>
{
    CleanDirectory(OutputDir);
    CleanDirectory(TargetDir);
});

Task("Build-NetCore")
    .Does(() =>
    {
        var path = MakeAbsolute(new DirectoryPath(SolutionFilePath));
        DotNetCoreBuild(path.FullPath, new DotNetCoreBuildSettings
        {
            Configuration = Configuration,
            NoRestore = false,
            DiagnosticOutput = true,
            MSBuildSettings = MsBuildSettings,
            Verbosity = DotNetCoreVerbosity.Minimal
        });
    });

Task("Run-NetCore-Unit-Tests")
    .IsDependentOn("Build-NetCore")
    .Does(() =>
    {
        foreach (string testProjectFilePath in NetCoreTestProjectsFilePaths)
        {
            DotNetCoreTest(
                testProjectFilePath,
                new DotNetCoreTestSettings()
                {
                    Configuration = Configuration,
                    NoBuild = false
                });
        }
    });

Task("Build-MSBuild")
    .IsDependentOn("Build-NetCore")
    .WithCriteria(() => IsRunningOnWindows())
    .Does(()=>
    {
        var buildSettings = new MSBuildSettings
        {
            Verbosity = Verbosity.Normal,
            ToolVersion = MSBuildToolVersion.VS2019,
            Configuration = Configuration,
            PlatformTarget = PlatformTarget.x64,
            Restore = true,
            MaxCpuCount = 0, // enable parallel builds
        };

        foreach (string projectFilePath in MSBuildProjectsFilePaths)
        {
            MSBuild(projectFilePath, buildSettings);
        }
    });

Task("Run-Unit-Tests")
    .IsDependentOn("Build-MSBuild")
    .WithCriteria(() => IsRunningOnWindows())
    .Does(() =>
    {
        var buildSettings = new MSBuildSettings
        {
            Verbosity = Verbosity.Normal,
            ToolVersion = MSBuildToolVersion.VS2019,
            Configuration = Configuration,
            PlatformTarget = PlatformTarget.x64,
            Restore = true,
        };

        foreach (string testProjectFilePath in TestProjectsFilePaths)
        {
            MSBuild(testProjectFilePath, buildSettings);
        }
    });

Task("Generate-CMake")
    .WithCriteria(() => IsRunningOnUnix())
    .IsDependentOn("Build-NetCore")
    .Does(() =>
    {
        var cmakeSettings = new CMakeSettings
        {
            Generator = "Unix Makefiles",
            OutputPath = $"{CMakeBuildDir}",
            SourcePath = ".",
        };

        CMake(cmakeSettings);
    });

Task("Build-CMake")
    .WithCriteria(() => IsRunningOnUnix())
    .IsDependentOn("Generate-CMake")
    .Does(() =>
    {
        var cmakeBuildTargets = new[]
        {
            // TODO: Add additional C++ build/test targets for Linux
            "Mlos.Core",
            "Mlos.UnitTest",
            "SmartCache",
            "SmartSharedChannel",
        };

        var settings = new CMakeBuildSettings
        {
            BinaryPath = $"{CMakeBuildDir}",
            Configuration = CMakeConfiguration,
            Options = new[]
            {
                "--jobs", // enable parallel builds using as many processes as CPUs
            },
            Targets = new[]
            {
                // Workaround a bug in how CMakeBuildSettings joins the targets
                // to be build with commas instead of spaces before passing it
                // to the "cmake --build" command.
                String.Join(" ", cmakeBuildTargets)
            },
        };

        CMakeBuild(settings);
    });

Task("Binplace-CMake")
    .WithCriteria(() => IsRunningOnUnix())
    .IsDependentOn("Build-CMake")
    .Does(() =>
    {
        var cmakeBuildTargets = new[]
        {
            "install",
        };

        var settings = new CMakeBuildSettings
        {
            BinaryPath = $"{CMakeBuildDir}",
            Configuration = CMakeConfiguration,
            Targets = new[]
            {
                String.Join(" ", cmakeBuildTargets)
            },
        };

        CMakeBuild(settings);
    });

Task("Test-CMake")
    .WithCriteria(() => IsRunningOnUnix())
    .IsDependentOn("Binplace-CMake")
    .Does(() =>
    {
        var cmakeTestTargets = new[]
        {
            // test is a virtual target that cmake generates for automatically
            // calling ctest for all the registered tests in the CMakeLists.txt
            "test",
        };

        var settings = new CMakeBuildSettings
        {
            BinaryPath = $"{CMakeBuildDir}",
            Configuration = CMakeConfiguration,
            Targets = new[]
            {
                String.Join(" ", cmakeTestTargets)
            },
        };

        CMakeBuild(settings);
    });

// Return list of files as nuget spec content from given input folder.
//
private IEnumerable<NuSpecContent> CollectFilesAsNugetContent(string inputDirPath, string nugetOutputDir, params string[] includeFilePatterns)
{
    // Make an absolute path to the input directory.
    //
    string inputDirFullPath = MakeAbsolute(new DirectoryPath(inputDirPath)).FullPath;

    if (!includeFilePatterns.Any())
    {
        includeFilePatterns = new[] { "*" };
    }

    foreach(string includeFilePattern in includeFilePatterns)
    {
        // Collect all the files.
        //
        FilePathCollection inputFiles = GetFiles($"{inputDirFullPath}/**/{includeFilePattern}");

        bool isFilePresent = false;

        foreach(var inputFile in inputFiles)
        {
            isFilePresent = true;

            yield return new NuSpecContent
            {
                Source = inputFile.FullPath,
                Target = IO.Path.Combine(nugetOutputDir, inputFile.FullPath.Substring(inputDirFullPath.Length + 1))
            };
        }

        if (!isFilePresent)
        {
            Information($"Unable to locate any files in folder {inputDirFullPath} using pattern {includeFilePattern}.");
            throw new FileNotFoundException($"Unable to locate any files in folder {inputDirFullPath} using pattern {includeFilePattern}.");
        }
    }
}

Task("Create-Nuget-Package")
    .Does(()=>
    {
        var sourcePath = new DirectoryPath("./source/Mlos.Core");
        var SourceFullPath = MakeAbsolute(sourcePath).FullPath;

        NuSpecContent[] sourceFiles = Enumerable.Empty<NuSpecContent>()
            .Concat(CollectFilesAsNugetContent("./source/Mlos.Core/", "source/Mlos.Core/", "*.cpp", "*.h", "*.inl"))
            .Concat(CollectFilesAsNugetContent($"./out/Mlos.CodeGen.out/{Configuration}/Mlos.Core", "codegen/Mlos.Core", "*.h", "*.cs"))
            .Concat(CollectFilesAsNugetContent($"./out/dotnet/source/Mlos.Agent.Server/{ObjectDirectory}/{AnyCPUPlatform}/", "bin/Mlos.Agent.Server", "*"))
            .Concat(CollectFilesAsNugetContent($"./out/dotnet/source/Mlos.SettingsSystem.CodeGen/{ObjectDirectory}/{AnyCPUPlatform}/", "bin/Mlos.SettingsSystem.CodeGen", "*"))
            .Concat(CollectFilesAsNugetContent($"./out/dotnet/source/Mlos.NetCore/{ObjectDirectory}/{AnyCPUPlatform}/", "lib/netcoreapp3.1", "Mlos.NetCore.*"))
            .Concat(CollectFilesAsNugetContent($"./out/dotnet/source/Mlos.NetCore/{ObjectDirectory}/{AnyCPUPlatform}/", "lib/netcoreapp3.1", "Mlos.SettingsSystem.Attributes.*"))
            .ToArray();

        var mlosNetCoreSpec = sourceFiles.FirstOrDefault(r=> IO.Path.GetFileName(r.Source) == "Mlos.NetCore.dll");

        if (mlosNetCoreSpec == null)
        {
            Information("Unable to locate Mlos.NetCore.dll");
            throw new FileNotFoundException("Unable to locate Mlos.NetCore.dll");
        }

        // Get version from Mlos.NetCore.dll.
        //
        string assemblyPath = mlosNetCoreSpec.Source;
        var asmVersion = FileVersionInfo.GetVersionInfo(assemblyPath);

        // Create nuget package in Taget directory.
        //
        NuGetPack("./nuspec/Mlos.nuspec",
            new NuGetPackSettings
            {
                Version = asmVersion.FileVersion,
                OutputDirectory = TargetDir,
                Symbols = false,
                NoPackageAnalysis = true,
                Files = sourceFiles
            });
    });


// Create a dockerfile with the SA_PASSWORD set.
//
Task("Generate-MlosModelServices-Dockerfile")
    .Does(()=>
    {
        var originalDockerfileContents = IO.File.ReadAllText(OriginalDockerfileFilePath);
        var testDockerfileContents = originalDockerfileContents.Replace("DEFAULT_SA_PASSWORD", SqlPassword);
        IO.Directory.CreateDirectory(DockerTestDirectory);
        IO.File.WriteAllText(TestDockerfileFilePath, testDockerfileContents);
    });


Task("Build-Docker-Image")
    .WithCriteria(() => IsRunningOnWindows())
    .IsDependentOn("Build-NetCore")
    .IsDependentOn("Build-MSBuild")
    .Does(()=>
    {
        var originalWorkingDirectory = IO.Directory.GetCurrentDirectory();
        var dockerBuildWorkingDirectory = IO.Path.Combine(originalWorkingDirectory, "source", "Mlos.Python");
        IO.Directory.SetCurrentDirectory(dockerBuildWorkingDirectory);
        var dockerBuildSettings = new DockerImageBuildSettings
        {
            Tag = new[] {"mssql-server-linux-with-mlos-python:latest"}, // TODO: add version
            File = "Docker/Dockerfile",
            BuildArg = new[] {$"SA_PASSWORD={SqlPassword}"}
        };

        DockerBuild(dockerBuildSettings, ".");
        IO.Directory.SetCurrentDirectory(originalWorkingDirectory);
    });

Task("Test-Docker-E2E")
    .WithCriteria(() => IsRunningOnWindows())
    .IsDependentOn("Build-Docker-Image")
    .Does(()=>
    {
        var containerName = "MlosOptimizerService";

        // 1. Start Docker Container.
        //
        var runContainerSettings = new DockerContainerRunSettings
        {
            Detach = true,
            Publish = new [] {"1433:1433"},
            Name = containerName
        };

        Console.WriteLine($"Starting {containerName} Container");
        string firstLineOfOutput = DockerRun(
            settings: runContainerSettings,
            image: DockerImageName,
            command: string.Empty
        );
        Console.WriteLine($"Beginning of container output: {firstLineOfOutput}");

        System.Threading.Thread.Sleep(TimeSpan.FromSeconds(10)); // TODO: despite increasing the connection timeouts this still appears necessary. Figure out how to remove it.

        // 2. Start Mlos.Agent.Server + Spinlock.
        //
        string mlosAgentPath = GetBuildOutputFilePath("source/Mlos.Agent.Server", "Mlos.Agent.Server.exe");

        string sqlConnectionDetailsJsonFilePath = GetBuildOutputFilePath("source/Mlos.Model.Services", "ModelsDb/SampleModelsDatabaseConnectionDetails.json");

        string testExecPath = GetBuildOutputFilePath("source/Examples/SmartCache", "SmartCache.exe");

        ProcessArgumentBuilder Arguments = new ProcessArgumentBuilder();
        Arguments.Append(testExecPath);
        Arguments.Append(sqlConnectionDetailsJsonFilePath);

        int exitCode = StartProcess(
            fileName: mlosAgentPath,
            settings: new ProcessSettings
            {
                Arguments = Arguments,
                EnvironmentVariables = new Dictionary<string, string>()
                {
                    { "SQL_PASSWORD", SqlPassword }
                },
            }
        );

        if (exitCode != 0)
        {
            throw new Exception($"Mlos.Agent.Server process exited with exit code: {exitCode}.");
        }

        // 3. Stop Docker Container.
        //
        DockerStop(containers: new[] { containerName });

        // 4. Remove Container.
        //
        DockerRm(containers: new[] { containerName });
    });

//
// TASK TARGETS
//

Task("Default")
    .IsDependentOn("Run-NetCore-Unit-Tests")
    .IsDependentOn("Run-Unit-Tests")
    .IsDependentOn("Test-CMake")
    .IsDependentOn("Generate-MlosModelServices-Dockerfile");

//    .IsDependentOn("Create-Nuget-Package")
//    .IsDependentOn("Test-Docker-E2E");

//
// EXECUTION
//

RunTarget(Target);
