// -----------------------------------------------------------------------
// <copyright file="CSharpObjectGetVariableDataSizeCodeWriter.cs" company="Microsoft Corporation">
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
    /// Generates a method which calculates object variable data size.
    /// </summary>
    /// <remarks>
    /// Length is sizeof the object, increased by size of the data stored in the variable length fields.
    /// </remarks>
    internal class CSharpObjectGetVariableDataSizeCodeWriter : CSharpCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsCodegenType();

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            WriteOpenTypeDeclaration(sourceType);

            WriteBlock($@"
                ulong global::Mlos.Core.ICodegenType.GetVariableDataSize()
                {{
                    ulong dataSize = 0;");
            WriteLine();

            IndentationLevel++;
        }

        /// <inheritdoc/>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine("return dataSize;");
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

            if (cppField.FieldInfo.IsFixedSizedArray())
            {
                // Serialize fixed length array.
                //
                var arrayAttribute = cppField.FieldInfo.GetCustomAttribute<FixedSizeArrayAttribute>();

                WriteLine($"dataSize = this.{cppField.FieldInfo.Name}.GetVariableDataSize({arrayAttribute.Length});");
            }
            else
            {
                string fieldName = cppField.FieldInfo.Name;

                WriteLine($"dataSize += ((global::Mlos.Core.ICodegenType){fieldName}).GetVariableDataSize();");
            }

            WriteLine();
        }
    }
}
