// -----------------------------------------------------------------------
// <copyright file="CSharpProxyCompareKeyCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpObjectExchangeCodeWriters
{
    /// <summary>
    /// Code writer class for CSharp ICodegenProxy implementation.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpProxyCompareKeyCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            WriteLine($"namespace {Constants.ProxyNamespace}.{@namespace}");
            WriteLine("{");

            ++IndentationLevel;
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            --IndentationLevel;
            WriteLine($"}} // end namespace {Constants.ProxyNamespace}.{@namespace}");

            WriteLine();
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType.DeclaringType);

            string typeName = sourceType.Name;

            WriteBlock($@"
                public partial struct {typeName}
                {{
                    public bool CompareKey(ICodegenProxy proxy)
                    {{
                        bool result = true;
                        var instance = ({typeName})proxy;");

            IndentationLevel += 2;
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
            if (!cppField.FieldInfo.IsPrimaryKey())
            {
                // The field is not a primary key, ignore it.
                //
                return;
            }

            string fieldName = cppField.FieldInfo.Name;

            WriteLine($"result &= this.{fieldName} == instance.{fieldName};");
        }
    }
}
