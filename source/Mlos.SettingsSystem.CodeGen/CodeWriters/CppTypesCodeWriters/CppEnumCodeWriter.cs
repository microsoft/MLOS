// -----------------------------------------------------------------------
// <copyright file="CppEnumCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Reflection;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppTypesCodeWriters
{
    /// <summary>
    /// Code writer class which generates a Cpp Enum type.
    /// </summary>
    internal class CppEnumCodeWriter : CppCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType) => sourceType.IsEnum;

        /// <inheritdoc />
        public override void WriteBeginFile()
        {
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
        }

        /// <inheritdoc />
        public override void BeginVisitType(Type sourceType)
        {
            Type enumUnderlyingType = sourceType.GetEnumUnderlyingType();

            string enumCppUnderlyingType = CppTypeMapper.GetCppFullTypeName(enumUnderlyingType);

            string cppClassName = sourceType.Name;

            WriteLine($"enum class {cppClassName} : {enumCppUnderlyingType}");
            WriteLine("{");

            IndentationLevel++;

            foreach (FieldInfo fieldInfo in sourceType.GetFields())
            {
                if (!fieldInfo.FieldType.IsEnum)
                {
                    // Skip invalid entries.
                    //
                    continue;
                }

                WriteLine($"{fieldInfo.Name} = {fieldInfo.GetRawConstantValue()},");
            }
        }

        /// <inheritdoc />
        public override void VisitField(CppField cppField)
        {
            // Nothing.
            //
        }
    }
}
