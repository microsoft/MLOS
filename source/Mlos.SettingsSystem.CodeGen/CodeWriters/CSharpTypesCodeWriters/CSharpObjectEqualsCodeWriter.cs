// -----------------------------------------------------------------------
// <copyright file="CSharpObjectEqualsCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpTypesCodeWriters
{
    /// <summary>
    /// Code writer class for CSharp ICodegenProxy implementation.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpObjectEqualsCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            string typeFullName = sourceType.GetTypeFullName();

            WriteBlock($@"
                /// <summary>
                /// Operator ==.
                /// </summary>
                /// <param name=""left""></param>
                /// <param name=""right""></param>
                /// <returns></returns>
                public static bool operator ==({typeFullName} left, {typeFullName} right) => left.Equals(right);

                /// <summary>
                /// Operator !=.
                /// </summary>
                /// <param name=""left""></param>
                /// <param name=""right""></param>
                /// <returns></returns>
                public static bool operator !=({typeFullName} left, {typeFullName} right) => !(left == right);

                /// <inheritdoc />
                public override bool Equals(object obj)
                {{
                    if (!(obj is {typeFullName}))
                    {{
                        return false;
                    }}

                    return Equals(({typeFullName})obj);
                }}

                /// <inheritdoc />
                public override int GetHashCode() => 0;

                /// <inheritdoc/>
                public bool Equals({typeFullName} other)
                {{
                    bool result = true;");

            IndentationLevel++;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine();
            WriteLine("return result;");
            IndentationLevel--;

            WriteLine("}");

            WriteCloseTypeDeclaration(sourceType);
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            string fieldName = cppField.FieldInfo.Name;

            WriteLine($"result &= this.{fieldName} == other.{fieldName};");
        }
    }
}
