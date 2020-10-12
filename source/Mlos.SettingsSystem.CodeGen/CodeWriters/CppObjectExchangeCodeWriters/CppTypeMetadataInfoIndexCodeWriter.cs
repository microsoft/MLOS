// -----------------------------------------------------------------------
// <copyright file="CppTypeMetadataInfoIndexCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Cpp type metadata code writer.
    /// Generates info methods for each type.
    /// </summary>
    /// <remarks>
    /// <![CDATA[
    /// template <> static constexpr uint32_t CodegenTypeIndex();
    /// returns a index for given type.
    /// ]]>
    /// </remarks>
    internal class CppTypeMetadataInfoIndexCodeWriter : CppTypeTableCodeWriter
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="CppTypeMetadataInfoIndexCodeWriter"/> class.
        /// </summary>
        /// <param name="sourceTypesAssembly"></param>
        public CppTypeMetadataInfoIndexCodeWriter(Assembly sourceTypesAssembly)
            : base(sourceTypesAssembly)
        {
        }

        /// <inheritdoc />
        public override bool Accept(Type sourceType)
        {
            return sourceType.IsCodegenType();
        }

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// Proxy structures are defined in namespace Proxy.
        /// </remarks>
        public override void WriteBeginFile()
        {
            // Declare DispatchTableBaseIndex, this gets declared in client code where we combine multiple dispatch tables together.
            //
            WriteGlobalBeginNamespace();
            WriteLine("constexpr uint32_t DispatchTableBaseIndex();");
            WriteGlobalEndNamespace();

            WriteBlock($@"
                namespace {Constants.TypeMetadataInfoNamespace}
                {{
                template<typename T>
                static constexpr uint32_t CodegenTypeIndex();");
            WriteLine();
            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            IndentationLevel--;
            WriteLine($"}} // end {Constants.TypeMetadataInfoNamespace} namespace");
            WriteLine();
        }

        /// <summary>
        /// For a new structure, create a entry in matadata table.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void EndVisitType(Type sourceType)
        {
            // Type CppType is beeing generated and it is not yet available.
            // Create a full name from CSharp type.
            //
            string cppTypeFullName = CppTypeMapper.GenerateCppFullTypeName(sourceType);

            uint typeIndex = TypeMetadataMapper.GetTypeIndex(sourceType);

            // Write a link to next metadata object.
            //
            WriteBlock(@$"
                template<>
                constexpr uint32_t CodegenTypeIndex<{cppTypeFullName}>() {{ return {DispatchTableCppNamespace}::DispatchTableBaseIndex() + {typeIndex}; }}");
        }
    }
}
