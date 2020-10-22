// -----------------------------------------------------------------------
// <copyright file="CommandLineParser.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// Codegen command line parser class.
    /// </summary>
    public static class CommandLineParser
    {
        /// <summary>
        /// The expected output name of the command executable.
        /// </summary>
        private const string CmdName = "Mlos.SettingsSystem.CodeGen";

        /// <summary>
        /// Prints usage text to stdout on the cli and exits.
        /// </summary>
        /// <param name="msg">Optional error message to output to stderr.</param>
        private static void Usage(string msg = null)
        {
            if (msg != null)
            {
                Console.Error.WriteLine(msg);
            }

            Console.WriteLine($@"
                Usage: Provide a list of one or more SettingsRegistry.cs files to be internally built and processed:
                # {CmdName} --output-path=path/to/place/codegen/output/files/ --input-cs=path/to/SettingsRegistry1.cs;path/to/SettingsRegistry2.cs ...

                Options:
                --output-path
                    Path to a directory to place code generated file(s) in.

                --output-basename
                    Basename of the codegen files output.
                    Currently defaults to 'SettingsProvider_gen'.

                --input-cs
                    Comma separated list of C# SettingsRegistry files to internally compile before analyzing for codegen.
                    Option may also be repeated.
                    Incompatible with the --input-dll option.");

            Environment.Exit(1);
        }

        /// <summary>
        /// Handles parsing and validating CLI args.
        /// </summary>
        /// <param name="args"></param>
        /// <param name="inputDefs"></param>
        /// <param name="outputPath"></param>
        /// <param name="outputFileBasename"></param>
        internal static void ParseArgs(
            string[] args,
            out string[] inputDefs,
            out string outputPath,
            out string outputFileBasename)
        {
            string[] outputPaths;
            string[] outputBasenames;

            const char separator = ',';

            const string inputCsOpt = "--input-cs=";
            const string outputPathOpt = "--output-path=";
            const string outputBasenameOpt = "--output-basename=";

            IDictionary<string, string> optValues = new Dictionary<string, string>
            {
                [inputCsOpt] = string.Empty,
                [outputPathOpt] = string.Empty,
                [outputBasenameOpt] = string.Empty,
            };

            foreach (string arg in args)
            {
                if (arg.Equals("--help") || arg.Equals("-h") || arg.Equals("-?") || arg.Equals("/?") || arg.Equals("/h") || arg.Equals("/help"))
                {
                    // Usage options are special, abort immediately when we see them.
                    //
                    Usage();
                }
                else
                {
                    // Check the set of supported value options for a match.
                    //
                    string matchedOpt = null;
                    foreach (string opt in optValues.Keys)
                    {
                        if (arg.StartsWith(opt))
                        {
                            // can't modify it within the enumeration, so note it and break out of the loop
                            matchedOpt = opt;
                            break;
                        }
                    }

                    if (matchedOpt != null)
                    {
                        // Build up a string of comma separated values for the option.
                        //
                        string val = arg.Substring(matchedOpt.Length);
                        optValues[matchedOpt] += val + separator;
                    }
                    else
                    {
                        // All others should return an error.
                        //
                        Usage($"Unhandled argument: '{arg}'");
                    }
                }
            }

            // Split the strings back apart.
            //
            inputDefs = optValues[inputCsOpt].Split(separator).Where(str => !string.IsNullOrWhiteSpace(str)).ToArray();

            outputPaths = optValues[outputPathOpt].Split(separator).Where(str => !string.IsNullOrWhiteSpace(str)).ToArray();
            outputBasenames = optValues[outputBasenameOpt].Split(separator).Where(str => !string.IsNullOrWhiteSpace(str)).ToArray();

            // Check the arguments.
            //
            if (outputPaths.Length != 1)
            {
                Usage("ERROR: Missing or extra --output-path option.");
            }

            if (outputBasenames.Length == 0)
            {
                // Provide a default --output-basename
                //
                outputBasenames = new string[] { "SettingsProvider_gen" };
            }

            if (outputBasenames.Length != 1)
            {
                // We support only one basename option.
                //
                Usage("ERROR: Missing or extra --output-basename option.");
            }

            if (inputDefs.Length == 0)
            {
                // No input files.
                //
                Usage("ERROR: Missing --input-cs option.");
            }

            outputPath = outputPaths[0];
            outputFileBasename = outputBasenames[0];
        }
    }
}
