// -----------------------------------------------------------------------
// <copyright file="CppObjectEqualsCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppTypesCodeWriters
{
    /// <summary>
    /// Code writer class which generates the equality operator for C++ structures.
    /// </summary>
    internal class CppObjectEqualsCodeWriter : CppCodeWriter
    {
        /// <summary>
        /// Only interested in struct type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void WriteBeginFile()
        {
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            string cppTypeFullName = CppTypeMapper.GenerateCppFullTypeName(sourceType);

            WriteBlock($@"
                inline bool operator==(const {cppTypeFullName}& a, const {cppTypeFullName}& b)
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
            string fieldName = cppField.FieldInfo.Name;

            WriteLine($"result &= (a.{fieldName} == b.{fieldName});");
        }

        /// <inheritdoc />
        public override void VisitConstField(CppConstField cppConstField)
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
    }
}
