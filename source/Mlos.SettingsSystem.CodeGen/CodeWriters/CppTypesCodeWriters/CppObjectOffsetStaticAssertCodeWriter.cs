// -----------------------------------------------------------------------
// <copyright file="CppObjectOffsetStaticAssertCodeWriter.cs" company="Microsoft Corporation">
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
    /// Code writer class which generates static asserts to verify offset of cpp structure fields .
    /// </summary>
    internal class CppObjectOffsetStaticAssertCodeWriter : CppCodeWriter
    {
        /// <summary>
        /// Only interested in struct type.
        /// </summary>
        /// <param name="sourceType"></param>
        /// <returns></returns>
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void WriteBeginFile() => WriteLine();

        /// <inheritdoc />
        public override void WriteEndFile() => WriteLine();

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            WriteLine("namespace {");
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            WriteLine("} // end namespace anonymous");
            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            ++IndentationLevel;
        }

        /// <inheritdoc />
        public override void EndVisitType(Type sourceType)
        {
            --IndentationLevel;
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            string cppDeclaringTypeFullName = CppTypeMapper.GetCppFullTypeName(cppField.FieldInfo.DeclaringType);
            string fieldName = cppField.FieldInfo.Name;
            string actualOffsetText = $@"offsetof(struct {cppDeclaringTypeFullName}, {fieldName})";
            string assertionErrorMessage = $@"""Invalid offset""";

            WriteLine($@"static_assert({actualOffsetText} == {cppField.CppStructOffset}, {assertionErrorMessage});");
        }
    }
}
