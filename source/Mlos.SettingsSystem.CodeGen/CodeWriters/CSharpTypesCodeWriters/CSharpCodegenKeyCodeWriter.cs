// -----------------------------------------------------------------------
// <copyright file="CSharpCodegenKeyCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpTypesCodeWriters
{
    /// <summary>
    /// Code writer class for CSharp primary key.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpCodegenKeyCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType() && sourceType.HasPrimaryKey();

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            WriteLine($"namespace {@namespace}");
            WriteLine("{");

            ++IndentationLevel;
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            --IndentationLevel;
            WriteLine($"}} // end namespace {@namespace}");

            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            WriteBlock($@"
                public partial struct CodegenKey
                {{");

            IndentationLevel++;
            WriteLine();
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            IndentationLevel--;
            WriteLine("}");

            WriteCloseTypeDeclaration(sourceType);
        }

        /// <inheritdoc />
        public override void WriteComments(CodeComment codeComment)
        {
            foreach (string enumLineComment in codeComment.Summary.Split(new[] { Environment.NewLine }, StringSplitOptions.None))
            {
                string lineComment = $" {enumLineComment.Trim()}";
                WriteLine($"//{lineComment.TrimEnd()}");
            }

            WriteLine("//");
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            if (!cppField.FieldInfo.IsPrimaryKey())
            {
                // This field is not a primary key, ignore it.
                //
                return;
            }

            string fieldName = cppField.FieldInfo.Name;
            Type fieldType = cppField.FieldInfo.FieldType;
            string fieldTypeName = $"global::{fieldType.FullName}";

            WriteLine($"public {fieldTypeName} {fieldName};");
        }
    }
}
