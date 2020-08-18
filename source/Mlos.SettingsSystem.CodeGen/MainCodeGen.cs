// -----------------------------------------------------------------------
// <copyright file="MainCodeGen.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Microsoft.CodeAnalysis;

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.CodeGen.CodeWriters;
using Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters;
using Mlos.SettingsSystem.CodeGen.CodeWriters.CppTypesCodeWriters;
using Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpObjectExchangeCodeWriters;
using Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpTypesCodeWriters;

namespace Mlos.SettingsSystem.CodeGen
{
    /// <summary>
    /// The main executable class responsible for walking configs via Relection
    /// and calling into code generation handlers.
    /// </summary>
    public static class MainCodeGen
    {
        /// <summary>
        /// Main.
        /// </summary>
        /// <param name="args"></param>
        public static void Main(string[] args)
        {
            CommandLineParser.ParseArgs(
                args ?? Array.Empty<string>(),
                out string[] inputDefs,
                out string outputPath,
                out string outputFileBasename);

            Console.WriteLine($"Out in {outputPath}");
            foreach (string fileName in inputDefs)
            {
                Console.WriteLine($" + {fileName}");
            }

            GenerateCode(inputDefs, outputPath, outputFileBasename);
        }

        /// <summary>
        /// Generate code based on inputs and print to output files.
        /// </summary>
        /// <param name="inputDefs">Paths for source files.</param>
        /// <param name="outputPath">Location to store output files.</param>
        /// <param name="outputFileBasename">The basename used for all the output files.</param>
        public static void GenerateCode(string[] inputDefs, string outputPath, string outputFileBasename)
        {
            CodeGenCSharpCompiler compiler = new CodeGenCSharpCompiler();
            CompilerOutput compilerOutput = compiler.CompileFromFiles(inputDefs, outputPath);

            CodeCommentsReader codeComments = compilerOutput.CodeComments;
            Compilation compilation = compilerOutput.Compilation;
            Assembly sourceTypesAssembly = compilerOutput.Assembly;

            // Store C# compiler, used later to compute codegen type hash.
            //
            TypeMetadataMapper.Compilation = compilerOutput.Compilation;

            MultiCodeWriter codeWriter = GetMainCodeWriter(sourceTypesAssembly);

            var codeGenErrors = new List<CodegenError>();

            bool result = GenerateTypes(codeWriter, compilation, codeComments, codeGenErrors, sourceTypesAssembly);

            if (!result || codeGenErrors.Any())
            {
                PrintCodeGenErrorsAndExit(codeGenErrors);
            }

            if (!Directory.Exists(outputPath))
            {
                Directory.CreateDirectory(outputPath);
            }

            WriteOutputToFile(codeWriter, outputFileBasename, outputPath);
        }

        private static MultiCodeWriter GetMainCodeWriter(Assembly sourceTypesAssembly)
        {
            return new MultiCodeWriter(
                new CodeWriter[]
                {
                    new CppEnumCodeWriter(),                                                    // enum types
                    new CppProxyDeclarationCodeWriter(),                                        // proxy declaration
                    new CppObjectCodeWriter(),                                                  // basic structures
                    new CppObjectOffsetStaticAssertCodeWriter(),                                // verifies the offset
                    new CppProxyCodeWriter(),                                                   // proxy view of structures
                    new CppTypeReflectionTableCodeWriter(sourceTypesAssembly),                  // reflection, run time struct information
                    new CppTypeMetadataInfoIndexCodeWriter(sourceTypesAssembly),                // type metadata info, compile time struct information
                    new CppTypeMetadataInfoHashCodeWriter(),                                    // type metadata info, hash
                    new CppTypeMetadataCompareKeyCodeWriter(),                                  // compare keys
                    new CppTypeMetadataGetKeyHashCodeWriter(),                                  // calculate key hash
                    new CppObjectGetVariableDataSizeCodeWriter(),                               // calculate object variable data size
                    new CppObjectSerializationVariableDataCodeWriter(),                         // object serialization code
                    new CppObjectDeserializeRuntimeCallbackCodeWriter(),                        // deserialization runtime callbacks
                    new CppObjectDeserializeFunctionCallbackCodeWriter(sourceTypesAssembly),    // deserialization handlers callbacks, required by deserialization handlers
                    new CppObjectDeserializeHandlerCodeWriter(sourceTypesAssembly),             // object deserialization handlers
                    new CppObjectDeserializeEntryCountCodeWriter(sourceTypesAssembly),          // object deserialization element count
                    new CppProxyVerifyVariableDataCodeWriter(),                                 // cpp proxy verify correctness of the variable data
                    new CSharpObjectCodeWriter(),                                               // csharp type extends definition with default constructor
                    new CSharpCodegenKeyCodeWriter(),                                           // csharp codegen key type definition
                    new CSharpCodegenKeyMethodsCodeWriter(sourceTypesAssembly),                 // csharp codegen key ICodegenKey interface implementation
                    new CSharpObjectDeserializeHandlerCodeWriter(sourceTypesAssembly),          // csharp deserialize handlers
                    new CSharpObjectDispatchHandlerCodeWriter(sourceTypesAssembly),             // csharp dispatch handler
                    new CSharpObjectCodegenTypeCodeWriter(sourceTypesAssembly),                 // csharp type metadata info, type index, hash value
                    new CSharpObjectGetVariableDataSizeCodeWriter(),                            // csharp object get size of the object variable data
                    new CSharpObjectSerializationVariableDataCodeWriter(),                      // csharp object variable data serialization code
                    new CSharpObjectSerializationFixedPartCodeWriter(),                         // csharp object fixed part serialization code
                    new CSharpObjectUpdateCodeWriter(),                                         // csharp proxy copy values to codegen object
                    new CSharpProxyCodeWriter(sourceTypesAssembly),                             // csharp proxy properties
                    new CSharpObjectCompareKeyCodeWriter(),                                     // csharp proxy compare key with codegen type
                    new CSharpProxyCompareKeyCodeWriter(),                                      // csharp proxy compare key with proxy
                    new CSharpCodegenKeyCompareKeyCodeWriter(),                                 // csharp proxy compare codegen key
                    new CSharpProxyGetKeyHashValueCodeWriter(),                                 // csharp proxy get key hash value
                    new CSharpProxyVerifyVariableDataCodeWriter(),                              // csharp proxy verify correctness of the variable data
                });
        }

        private static bool GenerateTypes(CodeWriter codeWriter, Compilation compilation, CodeCommentsReader codeComments, List<CodegenError> codeGenErrors, Assembly sourceTypesAssembly)
        {
            bool result = true;

            codeWriter.WriteBeginFile();

            var typeCodeGenerator = new TypeCodeGenerator
            {
                CodeWriter = codeWriter,
                SourceCompilation = compilation,
                SourceCodeComments = codeComments,
                CodeGenErrors = codeGenErrors,
            };

            // CodeGen all the Mlos types.
            //
            foreach (Type sourceType in sourceTypesAssembly.GetTypes().Where(type => type.IsCodegenType()))
            {
                result &= typeCodeGenerator.GenerateType(sourceType);
            }

            codeWriter.WriteEndFile();

            return result;
        }

        private static void PrintCodeGenErrorsAndExit(List<CodegenError> codeGenErrors)
        {
            Console.Error.WriteLine("Codegen errors:");

            // Codegen failed, print errors to the console.
            //
            codeGenErrors.Cast<CodegenError>().ToList().ForEach(
                error =>
                {
                    if (!string.IsNullOrEmpty(error.FileLinePosition.Path))
                    {
                        Console.Error.WriteLine($"{error.FileLinePosition.Path}({error.FileLinePosition.StartLinePosition},{error.FileLinePosition.EndLinePosition}): error: {error.ErrorText}");
                    }
                });

            Environment.Exit(1);
        }

        private static void WriteOutputToFile(MultiCodeWriter codeWriter, string outputFileBasename, string outputPath)
        {
            // Write results to file(s).
            // Each entry contains a key (file prefix), and the value (StringBuilder with generated code).
            //
            foreach (var entry in codeWriter.GetOutput())
            {
                // To support incremental build, check to see if the output has changed before committing it its file.
                //
                string outputFileName = outputFileBasename + entry.Key;
                string outputFilePath = Path.Combine(outputPath, outputFileName);
                string outputString = entry.Value.ToString();

                if (!File.Exists(outputFilePath) || File.ReadAllText(outputFilePath) != outputString)
                {
                    Console.WriteLine($"Writing changes to {outputFilePath}.");
                    File.WriteAllText(outputFilePath, outputString);
                }
                else
                {
                    Console.WriteLine($"No changes to {outputFilePath}.");
                }
            }
        }
    }
}
