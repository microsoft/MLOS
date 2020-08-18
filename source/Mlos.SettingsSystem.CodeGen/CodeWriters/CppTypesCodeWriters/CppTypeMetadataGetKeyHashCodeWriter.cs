// -----------------------------------------------------------------------
// <copyright file="CppTypeMetadataGetKeyHashCodeWriter.cs" company="Microsoft Corporation">
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
    internal class CppTypeMetadataGetKeyHashCodeWriter : CodeWriter
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
            WriteBlock($@"
                namespace {Constants.TypeMetadataInfoNamespace}
                {{
                template<typename T, typename THash>
                uint32_t GetKeyHashValue(const T& v);");
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

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            string cppTypeFullName = CppTypeMapper.GenerateCppFullTypeName(sourceType);

            WriteBlock($@"
                template <typename THash>
                inline uint32_t GetKeyHashValue(const {cppTypeFullName}& v)
                {{
                    (void)v;
                    uint32_t hashValue = THash::GetHashValue(::TypeMetadataInfo::CodegenTypeHash<{cppTypeFullName}>());");

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
            WriteLine("return hashValue;");
            IndentationLevel--;
            WriteLine("}");
            WriteLine();
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            if (!cppField.FieldInfo.IsPrimaryKey())
            {
                // The field is not a primary key, ignore it.
                //
                return;
            }

            string fieldName = cppField.FieldInfo.Name;

            WriteLine($"hashValue = THash::CombineHashValue(hashValue, v.{fieldName});");
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