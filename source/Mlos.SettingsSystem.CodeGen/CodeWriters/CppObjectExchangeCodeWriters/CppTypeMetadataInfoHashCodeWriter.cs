// -----------------------------------------------------------------------
// <copyright file="CppTypeMetadataInfoHashCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Cpp type metadata code writer.
    /// Generates info methods for each type.
    /// </summary>
    /// <remarks>
    /// <![CDATA[
    /// template <> static constexpr uint32_t CodegenTypeHash();
    /// returns a index for given type.
    /// ]]>
    /// </remarks>
    internal class CppTypeMetadataInfoHashCodeWriter : CodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
        }

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        /// <remarks>
        /// Proxy structures are defined in namespace Proxy.
        /// </remarks>
        public override void WriteBeginFile()
        {
            // Declare a hash function.
            //
            WriteBlock(@$"
                namespace TypeMetadataInfo
                {{
                template<typename T>
                static constexpr uint64_t CodegenTypeHash();");
            WriteLine();

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            IndentationLevel--;
            WriteLine("} // end " + Constants.TypeMetadataInfoNamespace + " namespace");
            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
            string cppTypeFullName = CppTypeMapper.GenerateCppFullTypeName(sourceType);

            ulong typeHashValue = TypeMetadataMapper.GetTypeHashValue(sourceType);

            // Write a hash value.
            //
            WriteLine("template <>");
            WriteLine($"constexpr uint64_t CodegenTypeHash<{cppTypeFullName}>() {{ return 0x{typeHashValue:x}; }}");
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override string FilePostfix => "_base.h";
    }
}
