// -----------------------------------------------------------------------
// <copyright file="CSharpProxyVerifyVariableDataCodeWriter.cs" company="Microsoft Corporation">
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
    /// Writes CSharp codegen proxy variable data verification method.
    /// </summary>
    internal class CSharpProxyVerifyVariableDataCodeWriter : CSharpCodeWriter
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
                    bool ICodegenProxy.VerifyVariableData(ulong objectOffset, ulong totalDataSize, ref ulong expectedDataOffset)
                    {{
                        bool isValid = true;");

            IndentationLevel += 2;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine();
            WriteLine("return isValid;");
            IndentationLevel--;

            WriteLine("}");

            WriteCloseTypeDeclaration(sourceType);
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            if (!cppField.CppType.HasVariableData)
            {
                // Ignore field with sized size.
                //
                return;
            }

            // Variable length field.
            //
            WriteLine($"// Update variable length field : {cppField.FieldInfo.Name} {cppField.CppType.Name}");
            WriteLine("//");

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Serialize fixed length array.
                //
                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                WriteBlock($@"
                    if (isValid)
                    {{
                        isValid = this.{cppField.FieldInfo.Name}.VerifyVariableData({arrayAttribute.Length}, objectOffset + {cppField.CppStructOffset}, totalDataSize, ref expectedDataOffset);
                    }}");
            }
            else
            {
                WriteBlock($@"
                    if (isValid)
                    {{
                        isValid = ((global::Mlos.Core.ICodegenProxy)this.{cppField.FieldInfo.Name}).VerifyVariableData(objectOffset + {cppField.CppStructOffset}, totalDataSize, ref expectedDataOffset);
                    }}");
            }
        }
    }
}
