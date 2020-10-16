// -----------------------------------------------------------------------
// <copyright file="CodeGenCSharpCompiler.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Loader;

using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Emit;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// Helper CSharp compiler class.
    /// </summary>
    internal class CodeGenCSharpCompiler
    {
        /// <summary>
        /// Compiles multiple CSharp files into assembly.
        /// </summary>
        /// <param name="inputFiles"></param>
        /// <param name="outputPath"></param>
        /// <remarks>
        /// The method also returns a documentation created from the source code.
        /// </remarks>
        /// <returns></returns>
        internal CompilerOutput CompileFromFiles(string[] inputFiles, string outputPath)
        {
            string resultAssemblyDocFullPath = Path.Combine(outputPath, "SettingsRegistry.xml");
            Directory.CreateDirectory(Path.GetDirectoryName(resultAssemblyDocFullPath));
            string assemblyName = Path.GetFileNameWithoutExtension(outputPath);

            var syntaxTrees = inputFiles.Select(inputFile =>
            {
                string sourceContent = File.ReadAllText(inputFile);
                return CSharpSyntaxTree.ParseText(text: sourceContent, path: inputFile, encoding: System.Text.Encoding.ASCII);
            });

            var refPaths = new[]
            {
                typeof(object).GetTypeInfo().Assembly.Location,
                Assembly.GetAssembly(typeof(Attributes.BaseCodegenAttribute)).Location,
                Assembly.GetExecutingAssembly().Location,
                Path.Combine(Path.GetDirectoryName(typeof(System.Runtime.GCSettings).GetTypeInfo().Assembly.Location), "System.Runtime.dll"),
            };
            MetadataReference[] references = refPaths.Select(r => MetadataReference.CreateFromFile(r)).ToArray();

            // Compile as dynamic library and disable all warnings.
            //
            var compilationOptions = new CSharpCompilationOptions(
                OutputKind.DynamicallyLinkedLibrary,
                warningLevel: 0,
                optimizationLevel: OptimizationLevel.Debug,
                allowUnsafe: true);

            CSharpCompilation compilation = CSharpCompilation.Create(
               assemblyName: assemblyName,
               syntaxTrees: syntaxTrees,
               references: references,
               options: compilationOptions);

            Assembly outputAssembly;

            using (var peStream = new MemoryStream())
            using (var pdbStream = new MemoryStream())
            using (var xmlDocStream = new MemoryStream())
            {
                var emitOptions = new EmitOptions(
                        debugInformationFormat: DebugInformationFormat.PortablePdb,
                        includePrivateMembers: true);

                EmitResult emitResults = compilation.Emit(
                    peStream: peStream,
                    pdbStream: pdbStream,
                    xmlDocumentationStream: xmlDocStream,
                    options: emitOptions);

                // Rewind streams.
                //
                peStream.Seek(0, SeekOrigin.Begin);
                pdbStream.Seek(0, SeekOrigin.Begin);
                xmlDocStream.Seek(0, SeekOrigin.Begin);

                if (!emitResults.Success)
                {
                    emitResults.Diagnostics.ToList().ForEach(
                        error =>
                        {
                            Console.Error.WriteLine($"Location:{error.Location}");
                            Console.Error.WriteLine($"  Error: {error}");
                        });

                    Environment.Exit(1);
                }

                outputAssembly = AssemblyLoadContext.Default.LoadFromStream(peStream, pdbStream);

                var codeComments = new CodeCommentsReader();
                codeComments.LoadFromAssembly(xmlDocStream);

                return new CompilerOutput(outputAssembly, emitResults, codeComments, compilation);
            }
        }
    }

    /// <summary>
    /// Wrapper class to pass back internal compiler step results assemblies.
    /// </summary>
    internal struct CompilerOutput
    {
        /// <summary>
        /// Gets the compiled assembly.
        /// </summary>
        public Assembly Assembly { get; }

        /// <summary>
        /// Gets the compilation results.
        /// </summary>
        public EmitResult EmitResult { get; }

        /// <summary>
        /// Gets the code comments reader instance.
        /// </summary>
        public CodeCommentsReader CodeComments { get; }

        /// <summary>
        /// Gets the compiled syntax tree.
        /// </summary>
        public CSharpCompilation Compilation { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="CompilerOutput"/> struct.
        /// </summary>
        /// <param name="assembly"></param>
        /// <param name="emitResult"></param>
        /// <param name="codeComments"></param>
        /// <param name="compilation"></param>
        public CompilerOutput(Assembly assembly, EmitResult emitResult, CodeCommentsReader codeComments, CSharpCompilation compilation)
        {
            Assembly = assembly;
            EmitResult = emitResult;
            CodeComments = codeComments;
            Compilation = compilation;
        }
    }
}
