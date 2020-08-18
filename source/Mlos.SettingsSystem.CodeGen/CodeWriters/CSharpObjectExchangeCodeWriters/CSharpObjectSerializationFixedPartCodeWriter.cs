// -----------------------------------------------------------------------
// <copyright file="CSharpObjectSerializationFixedPartCodeWriter.cs" company="Microsoft Corporation">
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
    internal class CSharpObjectSerializationFixedPartCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            WriteBlock($@"
                void global::Mlos.Core.ICodegenType.SerializeFixedPart(IntPtr buffer, ulong objectOffset)
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
        public override void VisitField(CppField cppField)
        {
            // Always serialize fixed part of the type.
            //
            WriteLine($"// Fixed variable length field : {cppField.FieldInfo.Name} {cppField.CppType.Name}");
            WriteLine("//");

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Serialize fixed length array.
                //
                FixedSizeArrayAttribute arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                if (cppField.CppType.IsCodegenType)
                {
                    WriteLine($"this.{cppField.FieldInfo.Name}.SerializeFixedPartCodetypeArray({arrayAttribute.Length}, buffer, objectOffset + {cppField.CppStructOffset});");
                }
                else
                {
                    WriteLine($"this.{cppField.FieldInfo.Name}.SerializeFixedPartPrimitiveTypeArray({arrayAttribute.Length}, buffer, objectOffset + {cppField.CppStructOffset});");
                }
            }
            else
            {
                if (cppField.CppType.IsCodegenType)
                {
                    WriteLine($"((global::Mlos.Core.ICodegenType)this.{cppField.FieldInfo.Name}).SerializeFixedPart(buffer, objectOffset + {cppField.CppStructOffset});");
                }
                else
                {
                    WriteLine($"CodegenTypeExtensions.SerializeFixedPart(this.{cppField.FieldInfo.Name}, buffer, objectOffset + {cppField.CppStructOffset});");
                }
            }

            WriteLine();
        }
    }
}
