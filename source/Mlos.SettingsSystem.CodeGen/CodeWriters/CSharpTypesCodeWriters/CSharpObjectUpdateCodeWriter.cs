// -----------------------------------------------------------------------
// <copyright file="CSharpObjectUpdateCodeWriter.cs" company="Microsoft Corporation">
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
    /// Writes C# method to update values from the proxy.
    /// </summary>
    /// <remarks>
    /// Serialize variable length fields.
    /// </remarks>
    internal class CSharpObjectUpdateCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            string proxyTypeFullName = $"{Constants.ProxyNamespace}.{sourceType.GetTypeFullName()}";

            WriteBlock($@"
                public void Update(ICodegenProxy sourceProxy)
                {{
                    var proxy = ({proxyTypeFullName})sourceProxy;");

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
        public override void VisitField(CppField cppField)
        {
            string fieldName = cppField.FieldInfo.Name;

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Copy fixed length array.
                //
                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                // Use different routine if copying array of primitive elements or array of ICodegenType.
                //
                if (cppField.CppType.IsCodegenType)
                {
                    WriteLine($"{fieldName}.UpdatePropertyProxyArray(proxy.{fieldName}, {arrayAttribute.Length});");
                }
                else
                {
                    WriteLine($"{fieldName}.UpdateProxyArray(proxy.{fieldName}, {arrayAttribute.Length});");
                }
            }
            else if (cppField.CppType.IsCodegenType)
            {
                WriteLine($"{fieldName}.Update(proxy.{fieldName});");
            }
            else
            {
                WriteLine($"{fieldName} = proxy.{fieldName};");
            }
        }
    }
}
