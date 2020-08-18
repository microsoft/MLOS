// -----------------------------------------------------------------------
// <copyright file="CSharpObjectCompareKeyCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

using Mlos.SettingsSystem.Attributes;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CSharpObjectExchangeCodeWriters
{
    /// <summary>
    /// Code writer class for CSharp ICodegenProxy implementation.
    /// </summary>
    /// <remarks>
    /// Writes all properties.
    /// </remarks>
    internal class CSharpObjectCompareKeyCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            string proxyTypeFullName = $"{Constants.ProxyNamespace}.{sourceType.GetTypeFullName()}";

            WriteBlock($@"
                public bool CompareKey(ICodegenProxy proxy)
                {{
                    bool result = true;
                    var instance = ({proxyTypeFullName})proxy;");

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
