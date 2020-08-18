// -----------------------------------------------------------------------
// <copyright file="CSharpObjectSerializationVariableDataCodeWriter.cs" company="Microsoft Corporation">
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
    /// Writes CSharp type serialization code.
    /// </summary>
    /// <remarks>
    /// Serialize variable length fields.
    /// </remarks>
    internal class CSharpObjectSerializationVariableDataCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            CppType cppType = CppTypeMapper.GetCppType(sourceType);

            WriteBlock($@"
                    ulong global::Mlos.Core.ICodegenType.SerializeVariableData(IntPtr buffer, ulong objectOffset, ulong dataOffset)
                    {{
                        ulong totalDataSize = 0;");

            IndentationLevel++;

            if (cppType.HasVariableData)
            {
                WriteLine("ulong dataSize = 0;");
            }

            WriteLine();
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine("return totalDataSize;");
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

            // Variable data field.
            //
            WriteLine($"// Serialize variable data field : {cppField.FieldInfo.Name} {cppField.CppType.Name}");
            WriteLine("//");

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Serialize fixed length array.
                //
                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                WriteLine($"dataSize = this.{cppField.FieldInfo.Name}.SerializeVariableData({arrayAttribute.Length}, buffer, objectOffset + {cppField.CppStructOffset}, dataOffset);");
            }
            else
            {
                WriteLine($"dataSize = ((global::Mlos.Core.ICodegenType)this.{cppField.FieldInfo.Name}).SerializeVariableData(buffer, objectOffset + {cppField.CppStructOffset}, dataOffset);");
            }

            WriteLine("totalDataSize += dataSize;");
            WriteLine("dataOffset += dataSize;");
            WriteLine();
        }
    }
}
