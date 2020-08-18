// -----------------------------------------------------------------------
// <copyright file="CppProxyVerifyVariableDataCodeWriter.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

namespace Mlos.SettingsSystem.CodeGen.CodeWriters.CppObjectExchangeCodeWriters
{
    /// <summary>
    /// Generates a function which verifies variable data.
    /// </summary>
    internal class CppProxyVerifyVariableDataCodeWriter : CppCodeWriter
    {
        /// <inheritdoc />
        public override bool Accept(Type sourceType)
        {
            // Fixed size structures do not have variable data fields.
            // No custom serialization code is required.
            //
            CppType cppType = CppTypeMapper.GetCppType(sourceType);
            return cppType.HasVariableData;
        }

        /// <summary>
        /// Write beginning of the file.
        /// </summary>
        public override void WriteBeginFile()
        {
            WriteLine($"namespace {Constants.ObjectSerializationNamespace}");
            WriteLine("{");

            IndentationLevel++;
        }

        /// <inheritdoc />
        public override void WriteEndFile()
        {
            IndentationLevel--;
            WriteLine("};");
            WriteLine();
        }

        /// <inheritdoc />
        public override void WriteOpenTypeNamespace(string @namespace)
        {
            // Nothing.
            //
        }

        /// <inheritdoc />
        public override void WriteCloseTypeNamespace(string @namespace)
        {
            // Nothing.
            //
        }

        /// <summary>
        /// Write a specialization of the template function to calculate the length of the variable fields for the provided type.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void BeginVisitType(Type sourceType)
        {
            string cppElementTypeFullName = CppTypeMapper.GetCppProxyFullTypeName(sourceType);

            WriteBlock($@"
                template<>
                inline bool VerifyVariableData<{cppElementTypeFullName}>({cppElementTypeFullName} object, uint64_t objectOffset, uint64_t totalDataSize, uint64_t& expectedDataOffset)
                {{
                    bool isValid = true;");

            IndentationLevel++;
        }

        /// <summary>
        /// End the function, return the calculated length.
        /// </summary>
        /// <param name="sourceType"></param>
        public override void EndVisitType(Type sourceType)
        {
            WriteLine("return isValid;");
            IndentationLevel--;
            WriteLine("}");
            WriteLine();
        }

        /// <summary>
        /// For each variable data field, increase total size required to serialize the structure.
        /// </summary>
        /// <param name="cppField"></param>
        public override void VisitField(CppField cppField)
        {
            if (!cppField.CppType.HasVariableData)
            {
                // Ignore field with sized size.
                //
                return;
            }

            string fieldName = cppField.FieldInfo.Name;

            WriteBlock($@"
                if (isValid)
                {{
                    isValid = {Constants.ObjectSerializationNamespace}::VerifyVariableData(object.{fieldName}(), objectOffset + {cppField.CppStructOffset}, totalDataSize, expectedDataOffset);
                }}");
        }
    }
}
