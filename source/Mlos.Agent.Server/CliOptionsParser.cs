// -----------------------------------------------------------------------
// <copyright file="CliOptionsParser.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;

using CommandLine;
using CommandLine.Text;

namespace Mlos.Agent.Server
{
    /// <summary>
    /// A helper class for parsing the command line arguments fed to <see cref="MlosAgentServer.Main" /> and displaying help usage
    /// output if necessary.
    /// </summary>
    public static class CliOptionsParser
    {
        /// <summary>
        /// Parses the command line arguments fed to <see cref="MlosAgentServer.Main" />.
        /// Displays help output and forces a program exit upon errors.
        /// </summary>
        /// <param name="args">The input arguments to parse.</param>
        /// <param name="executablePath">The path to the executable found in the cli args.</param>
        /// <param name="optimizerUri">The optimizer uri found in the cli args.</param>
        /// <param name="settingsRegistryPath">The path to the settings registry folder.</param>
        public static void ParseArgs(
            string[] args,
            out string executablePath,
            out Uri optimizerUri,
            out string settingsRegistryPath)
        {
            string executableFilePath = null;
            Uri optimizerAddressUri = null;
            string settingsRegistryFolderPath = null;

            IEnumerable<string> extraArgs = null;

            using var cliOptsParser = new Parser(with => with.HelpWriter = null);
            var cliOptsParseResult = cliOptsParser.ParseArguments<CliOptions>(args)
                .WithParsed(parsedOptions =>
                {
                    executableFilePath = parsedOptions.Executable;
                    optimizerAddressUri = parsedOptions.OptimizerUri;
                    settingsRegistryFolderPath = parsedOptions.SettingsRegistryPath;
                    extraArgs = parsedOptions.ExtraArgs;
                });

            if (cliOptsParseResult.Tag == ParserResultType.NotParsed)
            {
                cliOptsParseResult.WithNotParsed(errs => ShowUsageHelp(
                    cliOptsParseResult,
                    errors: errs,
                    msg: "Failed to parse command line options."));
            }
            else if (extraArgs != null && extraArgs.Any())
            {
                ShowUsageHelp(cliOptsParseResult, msg: "ERROR: Unknown arguments: " + string.Join(" ", extraArgs));
            }

            // Populate the output variables
            //
            executablePath = executableFilePath;
            optimizerUri = optimizerAddressUri;
            settingsRegistryPath = settingsRegistryFolderPath;
        }

        /// <summary>
        /// Displays the help usage, possibly with some error messages, and then exits (non-zero).
        /// </summary>
        /// <param name="parserResult">The results from a CommandLine.Parser.ParseArguments() operation.</param>
        /// <param name="errors">An errors reported by the parserResult.</param>
        /// <param name="msg">An optional error message to accompany the output.</param>
        private static void ShowUsageHelp<T>(ParserResult<T> parserResult, IEnumerable<Error> errors = null, string msg = null)
        {
            if (msg != null)
            {
                Console.Error.WriteLine(msg);
                Console.Error.WriteLine();
            }

            if (errors == null)
            {
                errors = new List<Error>();
            }

            HelpText helpText = null;
            if (errors.IsVersion())
            {
                helpText = HelpText.AutoBuild(parserResult);
            }
            else
            {
                helpText = HelpText.AutoBuild(
                    parserResult,
                    onError: ht =>
                    {
                        return HelpText.DefaultParsingErrorsHandler(parserResult, ht);
                    },
                    e => e);
                helpText.AddNewLineBetweenHelpSections = true;
                helpText.AddPreOptionsLines(new[]
                    {
                        string.Empty,

                        // Use a single long line of text to let the help output get wrapped automatically for us.
                        "The Mlos.Agent.Server acts as an external agent for MLOS integrated components, allowing them to "
                        + "send it messages over shared memory, which it can process and use to interface with an optimizer "
                        + "service to tune the components over their shared memory communication channels.",
                        string.Empty,

                        // Indent the actual commands to make them stand out a bit more.
                        // Note: The help out preserves the indent across wrapping.
                        "usage mode 1:  Wait for an application to register over global shared memory, without an optimizer.",
                        "    dotnet Mlos.Agent.Server.dll",
                        string.Empty,

                        "usage mode 2:  Wait for an application to register over global shared memory, and prepare to "
                        + "communicate with an MLOS optimizer listening at the given Grpc URI.",
                        "    dotnet Mlos.Agent.Server.dll --optimizer-uri http://localhost:50051",
                        string.Empty,

                        "usage mode 3:  Start an executable to communicate over freshly prepared global shared memory.",
                        "    dotnet Mlos.Agent.Server.dll --executable path/to/executable --settings-registry-path path/to/settings_assemblies",
                        string.Empty,

                        "usage mode 4:  Start an executable to communicate over freshly prepared global shared memory and "
                        + "prepare to communicate with an MLOS optimizer listening at the given Grpc URI.",
                        "    dotnet Mlos.Agent.Server.dll --executable path/to/executable  --settings-registry-path path/to/settings_assemblies --optimizer-uri http://localhost:50051",
                        string.Empty,

                        "Note: the optimizer service used in these examples can be started using the 'start_optimizer_microservice "
                        + "launch --port 50051' command from the mlos Python module.",
                    });
            }

            Console.WriteLine(helpText);
            Environment.Exit(1);
        }

        /// <summary>
        /// The command line options for this application.
        /// </summary>
        private class CliOptions
        {
            [Option("executable", Required = false, Default = null, HelpText = "A path to an executable to start (e.g. 'target/bin/Release/SmartCache').")]
            public string Executable { get; set; }

            [Option("optimizer-uri", Required = false, Default = null, HelpText = "A URI to connect to the MLOS Optimizer service over GRPC (e.g. 'http://localhost:50051').")]
            public Uri OptimizerUri { get; set; }

            [Option("settings-registry-path", Required = false, Default = null, HelpText = "A path to a folder with the settings registry assemblies.")]
            public string SettingsRegistryPath { get; set; }

            /// <remarks>
            /// Just used to detect any extra arguments so we can throw a warning.
            /// See Also: https://github.com/microsoft/MLOS/issues/112.
            /// </remarks>
            [CommandLine.Value(0)]
            public IEnumerable<string> ExtraArgs { get; set; }
        }
    }
}
