// -----------------------------------------------------------------------
// <copyright file="CppTypeMetadataCompareKeyCodeWriter.cs" company="Microsoft Corporation">
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
    /// Generates a method to compare structure primary key.
    /// </summary>
    internal class CppTypeMetadataCompareKeyCodeWriter : CodeWriter
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
                    template<typename T>
                    bool CompareKey(const T& a, const T& b);");

            IndentationLevel++;
            WriteLine();
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
                template <>
                inline bool CompareKey<{cppTypeFullName}>(const {cppTypeFullName}& a, const {cppTypeFullName}& b)
                {{
                    (void)a;
                    (void)b;
                    bool result = true;");
            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
            WriteLine("return result;");
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

            WriteLine($"result &= (a.{fieldName} == b.{fieldName});");
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